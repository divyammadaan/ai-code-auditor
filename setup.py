from setuptools import setup, find_packages

setup(
    name="ai-code-auditor",
    version="0.1.0",
    description="Security vulnerability detection and secure code rewriting using PEFT fine-tuned LLMs",
    packages=find_packages(),
    python_requires=">=3.10",
)
