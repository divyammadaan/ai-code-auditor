#!/usr/bin/env python3
"""
Compare v2 and v3 model performance

This script compares the performance of v2 (Big-Vul only) and v3 (Big-Vul + Synthetic)
models across various metrics, with special focus on minority class improvements.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

def load_results(version):
    """Load evaluation results for a specific version"""
    results_file = f'results/evaluation_metrics_{version}.json'
    
    if not Path(results_file).exists():
        print(f"⚠️  Results file not found: {results_file}")
        return None
    
    with open(results_file) as f:
        return json.load(f)

def compare_overall_metrics(v2_results, v3_results):
    """Compare overall accuracy metrics"""
    print("\n" + "="*70)
    print("OVERALL METRICS COMPARISON")
    print("="*70)
    
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    
    print(f"\n{'Metric':<20} {'v2':<15} {'v3':<15} {'Improvement':<15}")
    print("-"*70)
    
    for metric in metrics:
        v2_val = v2_results.get(metric, 0)
        v3_val = v3_results.get(metric, 0)
        improvement = ((v3_val - v2_val) / v2_val * 100) if v2_val > 0 else 0
        
        print(f"{metric:<20} {v2_val:<15.2%} {v3_val:<15.2%} {improvement:+.1f}%")

def compare_per_cwe_accuracy(v2_results, v3_results):
    """Compare per-CWE accuracy with focus on minority classes"""
    print("\n" + "="*70)
    print("PER-CWE ACCURACY COMPARISON")
    print("="*70)
    
    v2_cwe = v2_results.get('per_cwe_accuracy', {})
    v3_cwe = v3_results.get('per_cwe_accuracy', {})
    
    # Minority classes that received synthetic data or oversampling
    minority_classes = ['CWE-190', 'CWE-416', 'CWE-189', 'CWE-362', 'CWE-125']
    
    print(f"\n{'CWE':<15} {'v2 Acc':<12} {'v3 Acc':<12} {'Improvement':<15} {'Status'}")
    print("-"*70)
    
    improvements = []
    
    for cwe in sorted(set(list(v2_cwe.keys()) + list(v3_cwe.keys()))):
        v2_acc = v2_cwe.get(cwe, 0)
        v3_acc = v3_cwe.get(cwe, 0)
        improvement = ((v3_acc - v2_acc) / v2_acc * 100) if v2_acc > 0 else 0
        
        status = ""
        if cwe in minority_classes:
            status = "🎯 Target"
            improvements.append((cwe, improvement))
        
        print(f"{cwe:<15} {v2_acc:<12.2%} {v3_acc:<12.2%} {improvement:+.1f}%{' '*8} {status}")
    
    # Summary for minority classes
    if improvements:
        avg_improvement = np.mean([imp for _, imp in improvements])
        print("\n" + "-"*70)
        print(f"Average improvement on target classes: {avg_improvement:+.1f}%")

def plot_comparison(v2_results, v3_results, output_path='results/v2_v3_comparison.png'):
    """Create visualization comparing v2 and v3"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Overall metrics
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    v2_vals = [v2_results.get(m, 0) for m in metrics]
    v3_vals = [v3_results.get(m, 0) for m in metrics]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    axes[0].bar(x - width/2, v2_vals, width, label='v2', alpha=0.8)
    axes[0].bar(x + width/2, v3_vals, width, label='v3', alpha=0.8)
    axes[0].set_xlabel('Metric')
    axes[0].set_ylabel('Score')
    axes[0].set_title('Overall Metrics: v2 vs v3')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Plot 2: Per-CWE accuracy for minority classes
    minority_classes = ['CWE-190', 'CWE-416', 'CWE-189', 'CWE-362', 'CWE-125']
    v2_cwe = v2_results.get('per_cwe_accuracy', {})
    v3_cwe = v3_results.get('per_cwe_accuracy', {})
    
    v2_minority = [v2_cwe.get(cwe, 0) for cwe in minority_classes]
    v3_minority = [v3_cwe.get(cwe, 0) for cwe in minority_classes]
    
    x = np.arange(len(minority_classes))
    
    axes[1].bar(x - width/2, v2_minority, width, label='v2', alpha=0.8)
    axes[1].bar(x + width/2, v3_minority, width, label='v3', alpha=0.8)
    axes[1].set_xlabel('CWE Class')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Minority Class Accuracy: v2 vs v3')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(minority_classes, rotation=45)
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Comparison chart saved: {output_path}")

def analyze_improvements(v2_results, v3_results):
    """Analyze where v3 improved over v2"""
    print("\n" + "="*70)
    print("IMPROVEMENT ANALYSIS")
    print("="*70)
    
    v2_cwe = v2_results.get('per_cwe_accuracy', {})
    v3_cwe = v3_results.get('per_cwe_accuracy', {})
    
    improvements = []
    regressions = []
    
    for cwe in v2_cwe.keys():
        if cwe in v3_cwe:
            diff = v3_cwe[cwe] - v2_cwe[cwe]
            if diff > 0:
                improvements.append((cwe, diff))
            elif diff < 0:
                regressions.append((cwe, diff))
    
    print("\n🎉 Top Improvements:")
    for cwe, diff in sorted(improvements, key=lambda x: -x[1])[:5]:
        print(f"  {cwe}: +{diff:.1%}")
    
    if regressions:
        print("\n⚠️  Regressions:")
        for cwe, diff in sorted(regressions, key=lambda x: x[1])[:5]:
            print(f"  {cwe}: {diff:.1%}")
    
    # Calculate overall impact
    total_improvement = sum(diff for _, diff in improvements)
    total_regression = sum(abs(diff) for _, diff in regressions)
    net_improvement = total_improvement - total_regression
    
    print(f"\n📊 Net Improvement: {net_improvement:.1%}")

def main():
    print("="*70)
    print("v2 vs v3 Model Comparison")
    print("="*70)
    
    # Load results
    print("\nLoading results...")
    v2_results = load_results('v2')
    v3_results = load_results('v3')
    
    if not v2_results:
        print("❌ v2 results not found. Please run evaluation on v2 model first.")
        return
    
    if not v3_results:
        print("❌ v3 results not found. Please run evaluation on v3 model first.")
        print("\nTo evaluate v3:")
        print("  1. Train v3 model: python models/finetune.py --config configs/training_config_v3.yaml")
        print("  2. Evaluate v3: python notebooks/02_baseline_evaluation.py --model v3")
        return
    
    # Compare metrics
    compare_overall_metrics(v2_results, v3_results)
    compare_per_cwe_accuracy(v2_results, v3_results)
    analyze_improvements(v2_results, v3_results)
    
    # Create visualization
    plot_comparison(v2_results, v3_results)
    
    print("\n" + "="*70)
    print("✅ Comparison Complete!")
    print("="*70)

if __name__ == '__main__':
    main()
