"""
Full evaluation pipeline: run all models on the test set and generate
comparison reports.

Usage:
    python scripts/run_evaluation.py --model all --output results/
    python scripts/run_evaluation.py --model finetuned --output results/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on the path when running as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
import yaml
from loguru import logger

from evaluation.compare import compare_models, plot_comparison, plot_cwe_distribution
from evaluation.metrics import print_metrics_summary
from evaluation.qualitative import run_qualitative_analysis

app = typer.Typer()


def load_test_records(test_path: str) -> list[dict]:
    records = []
    with open(test_path) as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return records


@app.command()
def main(
    model: str = typer.Option("all", help="Model to evaluate: zero_shot, few_shot, finetuned, all"),
    output: str = typer.Option("./results", help="Output directory for results"),
    config: str = typer.Option("configs/training_config.yaml", help="Config file path"),
    max_samples: Optional[int] = typer.Option(None, help="Limit evaluation to N samples"),
    skip_model_eval: bool = typer.Option(
        False, help="Skip model inference (use existing result files)"
    ),
):
    """Run the full evaluation pipeline."""
    with open(config) as f:
        cfg = yaml.safe_load(f)

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    test_path = Path(cfg["dataset"]["processed_path"]) / cfg["dataset"].get("test_file", "test.jsonl")

    if not test_path.exists():
        logger.error(f"Test file not found: {test_path}. Run preprocessing first.")
        raise typer.Exit(1)

    test_records = load_test_records(str(test_path))
    if max_samples:
        test_records = test_records[:max_samples]
    logger.info(f"Loaded {len(test_records)} test records")

    if not skip_model_eval:
        # Import model components
        from models.baseline import BaselineEvaluator
        from models.inference import CodeAuditorModel
        from rag.vectorstore import VectorStore

        style_guide = "\n".join(cfg["prompt"]["style_guide_rules"])
        base_model_id = cfg["baseline"]["models"][0]["model_id"]

        # Load model
        logger.info(f"Loading model: {base_model_id}")
        vector_store = VectorStore()
        auditor = CodeAuditorModel(
            base_model_id=base_model_id,
            vector_store=vector_store,
        )
        evaluator = BaselineEvaluator(auditor, style_guide, output_dir=str(output_dir / "baseline"))

        all_results = {}

        if model in ("zero_shot", "all"):
            all_results["zero_shot"] = evaluator.evaluate_zero_shot(test_records, max_samples)

        if model in ("few_shot", "all"):
            all_results["few_shot_2"] = evaluator.evaluate_few_shot(test_records, n_shots=2, max_samples=max_samples)

        if model in ("finetuned", "all"):
            lora_path = cfg["training"]["output_dir"] if "training" in cfg else "./outputs/lora_adapter"
            if Path(lora_path).exists():
                finetuned = CodeAuditorModel(
                    base_model_id=base_model_id,
                    lora_adapter_path=lora_path,
                    vector_store=vector_store,
                )
                ft_evaluator = BaselineEvaluator(
                    finetuned, style_guide, output_dir=str(output_dir / "finetuned")
                )
                all_results["finetuned_lora"] = ft_evaluator.evaluate_zero_shot(test_records, max_samples)
            else:
                logger.warning(f"LoRA adapter not found at {lora_path}. Skipping fine-tuned eval.")
    else:
        # Load existing results from disk
        all_results = {}
        for results_file in output_dir.rglob("*_results.jsonl"):
            model_name = results_file.stem.replace("_results", "")
            all_results[model_name] = load_test_records(str(results_file))
            logger.info(f"Loaded {len(all_results[model_name])} results for {model_name}")

    if not all_results:
        logger.error("No results to evaluate.")
        raise typer.Exit(1)

    # Compare models
    comparison_df = compare_models(all_results, output_dir=str(output_dir))

    # Generate plots
    try:
        plot_comparison(comparison_df, output_dir=str(output_dir))
    except Exception as e:
        logger.warning(f"Plot generation failed: {e}")

    # Qualitative analysis for each model
    for model_name, results in all_results.items():
        run_qualitative_analysis(results, output_dir=str(output_dir), model_name=model_name)

    logger.success(f"Evaluation complete. Results saved to {output_dir}")


if __name__ == "__main__":
    app()
