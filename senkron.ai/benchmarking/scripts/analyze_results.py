"""
Benchmark Results Analyzer
Analyzes and visualizes benchmark results from multiple models
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict
import argparse


class BenchmarkAnalyzer:
    """Analyze and compare benchmark results"""
    
    def __init__(self, results_dir: str = "benchmark_results"):
        self.results_dir = Path(results_dir)
        self.results = []
        
    def load_all_results(self):
        """Load all JSON result files"""
        for json_file in self.results_dir.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.results.append(data)
        
        print(f"📂 Loaded {len(self.results)} benchmark results")
        return self
    
    def get_comparison_df(self) -> pd.DataFrame:
        """Create comparison dataframe"""
        rows = []
        for result in self.results:
            rows.append({
                'Model': result['model_name'].split('/')[-1],
                'Full Model': result['model_name'],
                'Task': result['task'],
                'Accuracy': result['accuracy'],
                'F1-Score': result.get('f1_score', 0),
                'Avg Latency (ms)': result['avg_latency_ms'],
                'Total Tests': result['total_tests'],
                'Correct': result['correct']
            })
        
        return pd.DataFrame(rows)
    
    def print_summary(self):
        """Print summary table"""
        df = self.get_comparison_df()
        
        print("\n" + "="*80)
        print("📊 BENCHMARK RESULTS SUMMARY")
        print("="*80 + "\n")
        
        # Group by task
        for task in df['Task'].unique():
            task_df = df[df['Task'] == task].sort_values('Accuracy', ascending=False)
            
            print(f"\n🎯 {task.upper()} TASK:")
            print("-" * 80)
            print(task_df.to_string(index=False))
        
        # Best model per task
        print("\n" + "="*80)
        print("🏆 BEST MODELS")
        print("="*80)
        
        for task in df['Task'].unique():
            task_df = df[df['Task'] == task]
            best = task_df.loc[task_df['Accuracy'].idxmax()]
            print(f"\n{task.upper()}:")
            print(f"  Model: {best['Full Model']}")
            print(f"  Accuracy: {best['Accuracy']:.2%}")
            print(f"  Latency: {best['Avg Latency (ms)']:.0f}ms")
    
    def plot_accuracy_comparison(self, save_path: str = None):
        """Plot accuracy comparison"""
        df = self.get_comparison_df()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Group by task
        tasks = df['Task'].unique()
        x = range(len(df))
        width = 0.35
        
        colors = {'router': 'skyblue', 'planner': 'lightcoral', 'e2e': 'lightgreen'}
        
        for task in tasks:
            task_df = df[df['Task'] == task].reset_index(drop=True)
            ax.bar(
                task_df.index,
                task_df['Accuracy'],
                label=task.capitalize(),
                color=colors.get(task, 'gray'),
                alpha=0.8
            )
        
        ax.set_ylabel('Accuracy', fontsize=12)
        ax.set_title('Model Accuracy Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df['Model'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 1.1)
        
        # Add value labels on bars
        for i, row in df.iterrows():
            ax.text(i, row['Accuracy'] + 0.02, f"{row['Accuracy']:.2%}", 
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Saved plot to {save_path}")
        
        plt.show()
    
    def plot_latency_vs_accuracy(self, save_path: str = None):
        """Plot latency vs accuracy scatter"""
        df = self.get_comparison_df()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        tasks = df['Task'].unique()
        colors = {'router': 'blue', 'planner': 'red', 'e2e': 'green'}
        
        for task in tasks:
            task_df = df[df['Task'] == task]
            ax.scatter(
                task_df['Avg Latency (ms)'],
                task_df['Accuracy'],
                label=task.capitalize(),
                color=colors.get(task, 'gray'),
                s=150,
                alpha=0.6,
                edgecolors='black'
            )
            
            # Add model labels
            for idx, row in task_df.iterrows():
                ax.annotate(
                    row['Model'],
                    (row['Avg Latency (ms)'], row['Accuracy']),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    alpha=0.8
                )
        
        ax.set_xlabel('Average Latency (ms)', fontsize=12)
        ax.set_ylabel('Accuracy', fontsize=12)
        ax.set_title('Latency vs Accuracy Trade-off', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # Ideal region (low latency, high accuracy)
        ax.axhline(y=0.9, color='green', linestyle='--', alpha=0.3, label='Target Accuracy (90%)')
        ax.axvline(x=1000, color='orange', linestyle='--', alpha=0.3, label='Target Latency (1s)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Saved plot to {save_path}")
        
        plt.show()
    
    def generate_report(self, output_file: str = "benchmark_report.md"):
        """Generate markdown report"""
        df = self.get_comparison_df()
        
        report = []
        report.append("# 📊 Model Benchmark Report\n")
        report.append(f"**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total Models Tested**: {len(df)}\n")
        report.append("\n---\n")
        
        # Summary table
        report.append("\n## 📈 Results Summary\n")
        report.append("\n" + df.to_markdown(index=False) + "\n")
        
        # Best models
        report.append("\n## 🏆 Best Models by Task\n")
        for task in df['Task'].unique():
            task_df = df[df['Task'] == task]
            best = task_df.loc[task_df['Accuracy'].idxmax()]
            
            report.append(f"\n### {task.upper()}\n")
            report.append(f"- **Model**: {best['Full Model']}\n")
            report.append(f"- **Accuracy**: {best['Accuracy']:.2%}\n")
            report.append(f"- **F1-Score**: {best['F1-Score']:.3f}\n")
            report.append(f"- **Avg Latency**: {best['Avg Latency (ms)']:.0f}ms\n")
        
        # Recommendations
        report.append("\n## 💡 Recommendations\n")
        
        # Best accuracy
        best_acc = df.loc[df['Accuracy'].idxmax()]
        report.append(f"\n### Highest Accuracy\n")
        report.append(f"**{best_acc['Full Model']}** achieves {best_acc['Accuracy']:.2%} accuracy on {best_acc['Task']} task.\n")
        
        # Best latency
        best_lat = df.loc[df['Avg Latency (ms)'].idxmin()]
        report.append(f"\n### Lowest Latency\n")
        report.append(f"**{best_lat['Full Model']}** has the lowest latency at {best_lat['Avg Latency (ms)']:.0f}ms.\n")
        
        # Best trade-off (score = accuracy - normalized_latency)
        df_copy = df.copy()
        df_copy['normalized_latency'] = df_copy['Avg Latency (ms)'] / df_copy['Avg Latency (ms)'].max()
        df_copy['score'] = df_copy['Accuracy'] - 0.3 * df_copy['normalized_latency']
        best_tradeoff = df_copy.loc[df_copy['score'].idxmax()]
        
        report.append(f"\n### Best Overall (Accuracy + Speed)\n")
        report.append(f"**{best_tradeoff['Full Model']}** offers the best balance of accuracy ({best_tradeoff['Accuracy']:.2%}) ")
        report.append(f"and latency ({best_tradeoff['Avg Latency (ms)']:.0f}ms).\n")
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(report))
        
        print(f"📄 Report saved to {output_file}")
        
        return ''.join(report)


def main():
    parser = argparse.ArgumentParser(description="Analyze benchmark results")
    parser.add_argument("--results-dir", type=str, default="benchmark_results")
    parser.add_argument("--output", type=str, default="benchmark_report.md")
    parser.add_argument("--plot", action="store_true", help="Generate plots")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = BenchmarkAnalyzer(args.results_dir)
    analyzer.load_all_results()
    
    # Print summary
    analyzer.print_summary()
    
    # Generate plots
    if args.plot:
        analyzer.plot_accuracy_comparison("accuracy_comparison.png")
        analyzer.plot_latency_vs_accuracy("latency_vs_accuracy.png")
    
    # Generate report
    analyzer.generate_report(args.output)
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
