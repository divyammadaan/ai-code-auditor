"""
QLoRA fine-tuning of CodeLlama / DeepSeek-Coder on the Big-Vul dataset.

Why QLoRA?
  - 4-bit NF4 quantization reduces memory from ~28GB (full fp16) to ~8GB
  - LoRA adapters add only ~0.5% extra trainable parameters (r=16)
  - Achieves >95% of full fine-tune quality at a fraction of the cost
  - Enables training on a single consumer GPU (24GB VRAM) or Colab A100

Training objective: Causal language modeling on instruction-formatted prompts.
The model learns to generate structured audit reports given vulnerable code.
"""

from __future__ import annotations

import os
from pathlib import Path

import torch
import yaml
from datasets import Dataset, load_dataset
from loguru import logger
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer


def load_config(config_path: str = "configs/lora_config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_tokenizer(model_id: str) -> AutoTokenizer:
    """Load tokenizer with padding token set (required for batched training)."""
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    # LLaMA-based models don't have a pad token by default
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "right"  # Prevent warnings with fp16
    return tokenizer


def load_quantized_model(model_id: str, quant_cfg: dict) -> AutoModelForCausalLM:
    """Load model in 4-bit NF4 quantization for QLoRA."""
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=quant_cfg["load_in_4bit"],
        bnb_4bit_quant_type=quant_cfg["bnb_4bit_quant_type"],
        bnb_4bit_compute_dtype=getattr(torch, quant_cfg["bnb_4bit_compute_dtype"]),
        bnb_4bit_use_double_quant=quant_cfg["bnb_4bit_use_double_quant"],
    )

    logger.info(f"Loading model: {model_id} (4-bit NF4 quantization)")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    model.config.use_cache = False  # Required for gradient checkpointing
    model.config.pretraining_tp = 1
    return model


def apply_lora(model: AutoModelForCausalLM, lora_cfg: dict) -> AutoModelForCausalLM:
    """Apply LoRA adapters to the quantized model."""
    # Prepare model for k-bit training (casts layer norms to fp32, etc.)
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        bias=lora_cfg["bias"],
        task_type=TaskType.CAUSAL_LM,
        target_modules=lora_cfg["target_modules"],
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def load_datasets(data_cfg: dict, tokenizer: AutoTokenizer) -> tuple[Dataset, Dataset]:
    """Load and tokenize the processed JSONL datasets."""
    processed_dir = Path(data_cfg["dataset_path"])

    train_dataset = load_dataset(
        "json",
        data_files=str(processed_dir / data_cfg["train_file"]),
        split="train",
    )
    val_dataset = load_dataset(
        "json",
        data_files=str(processed_dir / data_cfg["val_file"]),
        split="train",
    )

    logger.info(f"Train: {len(train_dataset):,} samples | Val: {len(val_dataset):,} samples")
    return train_dataset, val_dataset


def build_training_args(train_cfg: dict) -> TrainingArguments:
    """Build HuggingFace TrainingArguments from config."""
    return TrainingArguments(
        output_dir=train_cfg["output_dir"],
        num_train_epochs=train_cfg["num_train_epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=train_cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        gradient_checkpointing=train_cfg["gradient_checkpointing"],
        learning_rate=train_cfg["learning_rate"],
        weight_decay=train_cfg["weight_decay"],
        lr_scheduler_type=train_cfg["lr_scheduler_type"],
        warmup_ratio=train_cfg["warmup_ratio"],
        max_grad_norm=train_cfg["max_grad_norm"],
        fp16=train_cfg["fp16"],
        bf16=train_cfg["bf16"],
        logging_steps=train_cfg["logging_steps"],
        evaluation_strategy="steps",
        eval_steps=train_cfg["eval_steps"],
        save_strategy="steps",
        save_steps=train_cfg["save_steps"],
        save_total_limit=train_cfg["save_total_limit"],
        load_best_model_at_end=train_cfg["load_best_model_at_end"],
        metric_for_best_model=train_cfg["metric_for_best_model"],
        report_to=train_cfg["report_to"],
        seed=train_cfg["seed"],
        optim="paged_adamw_32bit",  # Memory-efficient optimizer for QLoRA
        group_by_length=True,       # Group similar-length sequences to reduce padding
    )


def run_finetuning(config_path: str = "configs/lora_config.yaml") -> None:
    """Full fine-tuning pipeline."""
    config = load_config(config_path)
    model_cfg = config["model"]
    quant_cfg = config["quantization"]
    lora_cfg = config["lora"]
    train_cfg = config["training"]
    data_cfg = config["data"]

    model_id = model_cfg["base_model"]

    # Load components
    tokenizer = load_tokenizer(model_id)
    model = load_quantized_model(model_id, quant_cfg)
    model = apply_lora(model, lora_cfg)

    # Load datasets
    train_dataset, val_dataset = load_datasets(data_cfg, tokenizer)

    # Training arguments
    training_args = build_training_args(train_cfg)

    # SFTTrainer handles prompt formatting and packing
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        args=training_args,
        dataset_text_field="text",          # The full instruction+completion field
        max_seq_length=data_cfg["max_seq_length"],
        packing=data_cfg["packing"],
    )

    logger.info("Starting fine-tuning...")
    trainer.train()

    # Save the LoRA adapter (not the full model — much smaller)
    output_dir = Path(train_cfg["output_dir"])
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.success(f"LoRA adapter saved to {output_dir}")

    # Save training metrics
    metrics = trainer.evaluate()
    logger.info(f"Final eval metrics: {metrics}")


if __name__ == "__main__":
    import typer

    app = typer.Typer()

    @app.command()
    def main(config: str = "configs/lora_config.yaml"):
        """Fine-tune CodeLlama with QLoRA on Big-Vul."""
        run_finetuning(config)

    app()
