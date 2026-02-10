"""
Multi-Provider Benchmarking Tool
Compare Anthropic, OpenAI, local models side-by-side on same benchmarks

Usage:
    python benchmark_multi_provider.py --providers anthropic,local --tasks all
"""

import json
import time
import pandas as pd
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import os

# Import providers
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_backend.mcp_server.providers import (
    create_anthropic_provider,
    create_huggingface_provider,
    GenerationResponse,
    ProviderError
)



@dataclass
class MultiProviderResult:
    """Result from multi-provider benchmark"""
    test_id: str
    test_type: str  # router, planner, finalizer, e2e
    input_text: str
    expected: Any
    predicted: Any
    correct: bool
    latency_ms: float
    
    # Provider info
    provider: str
    model: str
    
    # Token & cost tracking
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    
    # Metadata
    quantization: str = None
    error: str = None


class MultiProviderBenchmarker:
    """Benchmark runner supporting multiple providers"""
    
    def __init__(self, provider_configs: Dict[str, Dict]):
        """
        Initialize with provider configurations
        
        Args:
            provider_configs: Dict mapping provider names to config dicts
                Example: {
                    "anthropic": {"model": "claude-3-5-sonnet-20241022"},
                    "local_qwen": {"model": "Qwen/Qwen2.5-7B-Instruct", "quantization": "int4"}
                }
        """
        self.provider_configs = provider_configs
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        for name, config in self.provider_configs.items():
            try:
                if name.startswith("anthropic"):
                    provider = create_anthropic_provider(
                        model_name=config["model"],
                        max_tokens=config.get("max_tokens", 512),
                        temperature=config.get("temperature", 0.1)
                    )
                    self.providers[name] = provider
                    print(f"✅ Initialized Anthropic: {config['model']}")
                
                elif name.startswith("local"):
                    provider = create_huggingface_provider(
                        model_name=config["model"],
                        quantization=config.get("quantization", "int4"),
                        max_tokens=config.get("max_tokens", 512),
                        temperature=config.get("temperature", 0.1)
                    )
                    self.providers[name] = provider
                    print(f"✅ Initialized Local: {config['model']} ({config.get('quantization', 'int4')})")
                
            except Exception as e:
                print(f"❌ Failed to initialize {name}: {e}")
    
    def benchmark_router(self, test_data: List[Dict], provider_name: str) -> List[MultiProviderResult]:
        """Run router benchmark for a specific provider"""
        if provider_name not in self.providers:
            print(f"⚠️  Provider {provider_name} not available")
            return []
        
        provider = self.providers[provider_name]
        print(f"\n🧪 Router Benchmark - {provider_name} ({len(test_data)} tests)")
        
        ROUTER_PROMPT = """Classify this query into ONE category: APPT_CREATE, DOCTOR_INFO, APPT_CANCEL, KB_INFO, APPT_INFO, NO_TOOL_GENERAL

User query: {user_query}

Respond with ONLY the category name."""
        
        results = []
        valid_routes = ["APPT_CREATE", "DOCTOR_INFO", "APPT_CANCEL", "KB_INFO", "APPT_INFO", "NO_TOOL_GENERAL"]
        
        for i, test in enumerate(test_data, 1):
            prompt = ROUTER_PROMPT.format(user_query=test['input'])
            
            try:
                response = provider.generate(prompt, max_tokens=50)
                
                # Extract route from response
                predicted = response.text.strip().split('\n')[0].strip()
                if predicted not in valid_routes:
                    for route in valid_routes:
                        if route in response.text.upper():
                            predicted = route
                            break
                    else:
                        predicted = "UNKNOWN"
                
                correct = (predicted == test['expected_route'])
                
                result = MultiProviderResult(
                    test_id=test['test_id'],
                    test_type="router",
                    input_text=test['input'],
                    expected=test['expected_route'],
                    predicted=predicted,
                    correct=correct,
                    latency_ms=response.latency_ms,
                    provider=provider_name,
                    model=provider.config.model_name,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost_usd=response.cost_usd,
                    quantization=response.metadata.get("quantization"),
                    error=response.error
                )
                
                results.append(result)
                status = "✅" if correct else "❌"
                print(f"  [{i}/{len(test_data)}] {status} {test['test_id']}: {response.latency_ms:.0f}ms")
                
            except Exception as e:
                result = MultiProviderResult(
                    test_id=test['test_id'],
                    test_type="router",
                    input_text=test['input'],
                    expected=test['expected_route'],
                    predicted="ERROR",
                    correct=False,
                    latency_ms=0,
                    provider=provider_name,
                    model=provider.config.model_name,
                    error=str(e)
                )
                results.append(result)
                print(f"  [{i}/{len(test_data)}] ❌  {test['test_id']}: ERROR")
        
        # Print summary
        correct_count = sum(1 for r in results if r.correct)
        total_cost = sum(r.cost_usd for r in results)
        avg_latency = sum(r.latency_ms for r in results) / len(results)
        
        print(f"\n📊 {provider_name} Results:")
        print(f"  Accuracy: {correct_count}/{len(results)} ({correct_count/len(results):.2%})")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  Total Cost: ${total_cost:.4f}")
        
        return results
    
    def benchmark_all_providers(self, test_data: Dict[str, List], tasks: List[str] = ["router"]) -> Dict[str, List[MultiProviderResult]]:
        """
        Run benchmarks for all providers
        
        Args:
            test_data: Dictionary with test data for each task
            tasks: List of tasks to run (router, planner, etc.)
        
        Returns:
            Dictionary mapping provider names to results
        """
        all_results = {}
        
        for provider_name in self.providers.keys():
            provider_results = []
            
            if "router" in tasks and "router_tests" in test_data:
                router_res = self.benchmark_router(test_data['router_tests'], provider_name)
                provider_results.extend(router_res)
            
            # TODO: Add planner, finalizer, e2e benchmarks
            
            all_results[provider_name] = provider_results
        
        return all_results
    
    def export_unified_csv(self, all_results: Dict[str, List[MultiProviderResult]], output_dir: str):
        """Export all results to unified CSV"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Flatten results
        rows = []
        for provider_name, results in all_results.items():
            for result in results:
                rows.append(asdict(result))
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Save
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_file = output_path / f"MULTI_PROVIDER_RESULTS_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"\n💾 Unified results saved to: {csv_file}")
        print(f"   Total records: {len(df)}")
        
        # Generate comparison summary
        self._generate_comparison_report(df, output_path, timestamp)
        
        return csv_file
    
    def _generate_comparison_report(self, df: pd.DataFrame, output_path: Path, timestamp: str):
        """Generate comparison report"""
        report_lines = []
        report_lines.append("# Multi-Provider Benchmark Comparison")
        report_lines.append(f"\n**Generated**: {timestamp}\n")
        report_lines.append("---\n")
        
        # Overall stats
        report_lines.append("## Overall Statistics\n")
        report_lines.append(f"- Total tests: {len(df)}")
        report_lines.append(f"- Providers tested: {df['provider'].nunique()}")
        report_lines.append(f"- Tasks: {', '.join(df['test_type'].unique())}\n")
        
        # Per-provider comparison
        report_lines.append("## Provider Comparison\n")
        report_lines.append("| Provider | Model | Accuracy | Avg Latency (ms) | Total Cost ($) | Tests |")
        report_lines.append("|----------|-------|----------|------------------|----------------|-------|")
        
        for provider in df['provider'].unique():
            provider_df = df[df['provider'] == provider]
            accuracy = provider_df['correct'].mean()
            avg_latency = provider_df['latency_ms'].mean()
            total_cost = provider_df['cost_usd'].sum()
            test_count = len(provider_df)
            model = provider_df['model'].iloc[0]
            
            report_lines.append(
                f"| {provider} | {model} | {accuracy:.2%} | {avg_latency:.0f} | ${total_cost:.4f} | {test_count} |"
            )
        
        # Save report
        report_file = output_path / f"COMPARISON_REPORT_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"📄 Comparison report saved to: {report_file}")


def load_test_data(data_file: str = "../datasets/benchmark_dataset.json") -> Dict:
    """Load test dataset"""
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)



def main():
    parser = argparse.ArgumentParser(description="Multi-Provider Benchmark")
    parser.add_argument("--providers", type=str, default="local",
                       help="Comma-separated list: anthropic,local")
    parser.add_argument("--models", type=str, default="",
                       help="Comma-separated model names (optional)")
    parser.add_argument("--tasks", type=str, default="router",
                       help="Comma-separated tasks: router,planner,all")
    parser.add_argument("--dataset", type=str, default="../datasets/benchmark_dataset.json")
    parser.add_argument("--output-dir", type=str, default="../results")
    parser.add_argument("--anthropic-model", type=str, default="claude-3-5-sonnet-20241022")
    parser.add_argument("--local-model", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--quantization", type=str, default="int4")
    
    args = parser.parse_args()
    
    # Parse providers
    providers = args.providers.split(",")
    tasks = args.tasks.split(",")
    if "all" in tasks:
        tasks = ["router", "planner", "finalizer", "e2e"]
    
    # Build provider configs
    provider_configs = {}
    
    if "anthropic" in providers:
        provider_configs["anthropic"] = {
            "model": args.anthropic_model
        }
    
    if "local" in providers:
        provider_configs["local"] = {
            "model": args.local_model,
            "quantization": args.quantization
        }
    
    # Load test data
    print(f"📂 Loading test data from {args.dataset}...")
    test_data = load_test_data(args.dataset)
    
    # Initialize benchmarker
    benchmarker = MultiProviderBenchmarker(provider_configs)
    
    if not benchmarker.providers:
        print("❌ No providers initialized. Check your configuration.")
        return
    
    # Run benchmarks
    results = benchmarker.benchmark_all_providers(test_data, tasks)
    
    # Export results
    benchmarker.export_unified_csv(results, args.output_dir)
    
    # Print provider stats
    print("\n" + "="*80)
    print("🎯 PROVIDER STATISTICS")
    print("="*80)
    for provider_name, provider in benchmarker.providers.items():
        stats = provider.get_stats()
        print(f"\n{provider_name.upper()}:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Total tokens: {stats['total_tokens']:,}")
        print(f"  Total cost: ${stats['total_cost_usd']:.4f}")
        print(f"  Avg latency: {stats.get('avg_latency', 'N/A')}")
    
    print("\n✅ Multi-provider benchmark complete!")


if __name__ == "__main__":
    main()
