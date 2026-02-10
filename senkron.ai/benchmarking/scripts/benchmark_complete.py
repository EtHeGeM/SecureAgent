"""
Complete Pipeline Benchmarking - E2E + Finalizer + CSV Export
Tests full Router → Planner → Finalizer flow and exports all metrics to single CSV

Usage:
    python benchmark_complete.py --model "Qwen/Qwen2.5-7B-Instruct" --output-dir results
"""

import json
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import argparse

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sklearn.metrics import accuracy_score, f1_score

# Import from existing benchmark_runner
import sys
sys.path.append(str(Path(__file__).parent))
from benchmark_runner import ModelBenchmarker, BenchmarkResult, ModelBenchmarkSummary


@dataclass
class FinalizerResult(BenchmarkResult):
    """Finalizer-specific result"""
    response_quality: float = 0.0  # 0-1 score
    contains_expected_keywords: bool = False


@dataclass
class E2EResult(BenchmarkResult):
    """End-to-end result"""
    router_correct: bool = False
    planner_correct: bool = False
    finalizer_quality: float = 0.0
    total_latency_ms: float = 0.0
    pipeline_stage_reached: str = "router"  # router, planner, finalizer, complete


class CompleteBenchmarker(ModelBenchmarker):
    """Extended benchmarker with E2E and Finalizer support"""
    
    def benchmark_finalizer(self, test_data: List[Dict]) -> Tuple[List[FinalizerResult], ModelBenchmarkSummary]:
        """
        Benchmark finalizer (response generation)
        
        Tests natural language response generation based on tool results
        """
        print(f"\n🧪 Running Finalizer Benchmark ({len(test_data)} tests)...")
        
        FINALIZER_PROMPT_TEMPLATE = """You are a hospital appointment assistant. Generate a natural, helpful response in Turkish.

User query: {user_query}
Intent: {route}
Tool results: {tool_results}

Generate a friendly, informative response that addresses the user's request based on the tool results.
Be concise but complete. Use Turkish language."""

        results = []
        start_time = time.time()
        
        for i, test in enumerate(test_data, 1):
            prompt = FINALIZER_PROMPT_TEMPLATE.format(
                user_query=test['user_query'],
                route=test['route'],
                tool_results=json.dumps(test['tool_results'], ensure_ascii=False)
            )
            
            test_start = time.time()
            try:
                response = self.generate(prompt, max_tokens=256)
                latency = (time.time() - test_start) * 1000
                
                # Check if response contains expected keywords
                expected_keywords = test.get('expected_response_contains', [])
                contains_keywords = all(
                    any(keyword.lower() in response.lower() for keyword in [kw])
                    for kw in expected_keywords
                )
                
                # Calculate quality score (simple keyword matching)
                keyword_match_rate = sum(
                    1 for kw in expected_keywords 
                    if kw.lower() in response.lower()
                ) / max(len(expected_keywords), 1)
                
                # Response length check (not too short, not too long)
                length_score = 1.0 if 20 < len(response) < 500 else 0.5
                
                quality = (keyword_match_rate + length_score) / 2
                
                result = FinalizerResult(
                    test_id=test['test_id'],
                    input_text=test['user_query'],
                    expected=expected_keywords,
                    predicted=response,
                    correct=contains_keywords,
                    latency_ms=latency,
                    response_quality=quality,
                    contains_expected_keywords=contains_keywords
                )
                
            except Exception as e:
                result = FinalizerResult(
                    test_id=test['test_id'],
                    input_text=test['user_query'],
                    expected=test.get('expected_response_contains', []),
                    predicted="ERROR",
                    correct=False,
                    latency_ms=0,
                    response_quality=0.0,
                    contains_expected_keywords=False,
                    error=str(e)
                )
            
            results.append(result)
            print(f"  [{i}/{len(test_data)}] {'✅' if result.correct else '❌'} {test['test_id']}: Q={result.response_quality:.2f}, {result.latency_ms:.0f}ms")
        
        total_time = time.time() - start_time
        
        correct = sum(1 for r in results if r.correct)
        accuracy = correct / len(results)
        avg_latency = sum(r.latency_ms for r in results) / len(results)
        avg_quality = sum(r.response_quality for r in results) / len(results)
        
        summary = ModelBenchmarkSummary(
            model_name=self.model_name,
            task="finalizer",
            total_tests=len(results),
            correct=correct,
            accuracy=accuracy,
            avg_latency_ms=avg_latency,
            total_time_s=total_time,
            details=results
        )
        
        print(f"\n📊 Finalizer Results:")
        print(f"  Accuracy: {accuracy:.2%}")
        print(f"  Avg Quality: {avg_quality:.2f}/1.0")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        
        return results, summary
    
    def benchmark_e2e(self, test_data: List[Dict]) -> Tuple[List[E2EResult], ModelBenchmarkSummary]:
        """
        End-to-end benchmark (Router → Planner → Finalizer)
        
        Tests complete pipeline with simulated tool execution
        """
        print(f"\n🧪 Running E2E Benchmark ({len(test_data)} tests)...")
        
        results = []
        start_time = time.time()
        
        for i, test in enumerate(test_data, 1):
            total_start = time.time()
            
            try:
                # Stage 1: Router
                router_response = self._run_router(test['input'])
                router_correct = (router_response == test['expected_route'])
                
                if not router_correct:
                    # Pipeline failed at router
                    result = E2EResult(
                        test_id=test['test_id'],
                        input_text=test['input'],
                        expected=test['expected_outcome'],
                        predicted="failed_at_router",
                        correct=False,
                        latency_ms=0,
                        router_correct=False,
                        planner_correct=False,
                        finalizer_quality=0.0,
                        total_latency_ms=(time.time() - total_start) * 1000,
                        pipeline_stage_reached="router"
                    )
                    results.append(result)
                    print(f"  [{i}/{len(test_data)}] ❌ {test['test_id']}: Failed at ROUTER")
                    continue
                
                # Stage 2: Planner
                planner_response = self._run_planner(test['input'], router_response)
                planner_correct = (set(planner_response) == set(test['expected_tools_called']))
                
                if not planner_correct:
                    result = E2EResult(
                        test_id=test['test_id'],
                        input_text=test['input'],
                        expected=test['expected_outcome'],
                        predicted="failed_at_planner",
                        correct=False,
                        latency_ms=0,
                        router_correct=True,
                        planner_correct=False,
                        finalizer_quality=0.0,
                        total_latency_ms=(time.time() - total_start) * 1000,
                        pipeline_stage_reached="planner"
                    )
                    results.append(result)
                    print(f"  [{i}/{len(test_data)}] ⚠️  {test['test_id']}: Failed at PLANNER")
                    continue
                
                # Stage 3: Finalizer (simulated tool results)
                mock_tool_results = {}  # In real scenario, execute tools here
                finalizer_response = self._run_finalizer(test['input'], router_response, mock_tool_results)
                
                # Check if finalizer response contains expected keywords
                expected_keywords = test.get('expected_response_contains', [])
                finalizer_quality = sum(
                    1 for kw in expected_keywords 
                    if kw.lower() in finalizer_response.lower()
                ) / max(len(expected_keywords), 1)
                
                total_latency = (time.time() - total_start) * 1000
                
                # Overall success
                overall_success = router_correct and planner_correct and finalizer_quality >= 0.5
                
                result = E2EResult(
                    test_id=test['test_id'],
                    input_text=test['input'],
                    expected=test['expected_outcome'],
                    predicted="success" if overall_success else "partial",
                    correct=overall_success,
                    latency_ms=total_latency,
                    router_correct=True,
                    planner_correct=True,
                    finalizer_quality=finalizer_quality,
                    total_latency_ms=total_latency,
                    pipeline_stage_reached="complete"
                )
                
                results.append(result)
                status = "✅" if overall_success else "⚠️ "
                print(f"  [{i}/{len(test_data)}] {status} {test['test_id']}: Q={finalizer_quality:.2f}, {total_latency:.0f}ms")
                
            except Exception as e:
                result = E2EResult(
                    test_id=test['test_id'],
                    input_text=test['input'],
                    expected=test['expected_outcome'],
                    predicted="ERROR",
                    correct=False,
                    latency_ms=0,
                    router_correct=False,
                    planner_correct=False,
                    finalizer_quality=0.0,
                    total_latency_ms=0,
                    pipeline_stage_reached="error",
                    error=str(e)
                )
                results.append(result)
                print(f"  [{i}/{len(test_data)}] ❌ {test['test_id']}: ERROR")
        
        total_time = time.time() - start_time
        
        correct = sum(1 for r in results if r.correct)
        accuracy = correct / len(results)
        avg_latency = sum(r.total_latency_ms for r in results) / len(results)
        
        # Stage-wise metrics
        router_accuracy = sum(1 for r in results if r.router_correct) / len(results)
        planner_accuracy = sum(1 for r in results if r.planner_correct) / len(results)
        avg_finalizer_quality = sum(r.finalizer_quality for r in results) / len(results)
        
        summary = ModelBenchmarkSummary(
            model_name=self.model_name,
            task="e2e",
            total_tests=len(results),
            correct=correct,
            accuracy=accuracy,
            avg_latency_ms=avg_latency,
            total_time_s=total_time,
            details=results
        )
        
        print(f"\n📊 E2E Results:")
        print(f"  Overall Success: {accuracy:.2%}")
        print(f"  Router Accuracy: {router_accuracy:.2%}")
        print(f"  Planner Accuracy: {planner_accuracy:.2%}")
        print(f"  Finalizer Quality: {avg_finalizer_quality:.2f}/1.0")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        
        return results, summary
    
    def _run_router(self, user_input: str) -> str:
        """Run router classification"""
        prompt = f"""Classify this query into ONE category: APPT_CREATE, DOCTOR_INFO, APPT_CANCEL, KB_INFO, APPT_INFO, NO_TOOL_GENERAL

Query: {user_input}

Category:"""
        response = self.generate(prompt, max_tokens=20)
        # Extract route
        valid_routes = ["APPT_CREATE", "DOCTOR_INFO", "APPT_CANCEL", "KB_INFO", "APPT_INFO", "NO_TOOL_GENERAL"]
        for route in valid_routes:
            if route in response.upper():
                return route
        return "UNKNOWN"
    
    def _run_planner(self, user_input: str, route: str) -> List[str]:
        """Run planner tool selection"""
        prompt = f"""List tools needed (exact names): kb.search, doctor.search, doctor.profile, appointment.find_slots, appointment.create, appointment.info, appointment.cancel

Query: {user_input}
Route: {route}

Tools (JSON array):"""
        response = self.generate(prompt, max_tokens=100)
        
        # Extract tools
        tools = []
        all_tools = ["kb.search", "doctor.search", "doctor.profile", "appointment.find_slots", 
                     "appointment.create", "appointment.info", "appointment.cancel"]
        for tool in all_tools:
            if tool in response:
                tools.append(tool)
        return tools
    
    def _run_finalizer(self, user_input: str, route: str, tool_results: Dict) -> str:
        """Run finalizer response generation"""
        prompt = f"""Generate helpful Turkish response.

User: {user_input}
Intent: {route}
Results: {json.dumps(tool_results, ensure_ascii=False)}

Response:"""
        return self.generate(prompt, max_tokens=200)


def export_unified_csv(all_results: Dict[str, List], model_name: str, output_dir: str):
    """
    Export all benchmark results to a single unified CSV
    
    Args:
        all_results: Dict with keys 'router', 'planner', 'finalizer', 'e2e'
        model_name: Model identifier
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    model_safe = model_name.replace("/", "_")
    
    # Collect all results into unified format
    unified_data = []
    
    for test_type, results in all_results.items():
        for result in results:
            row = {
                'model': model_name,
                'timestamp': timestamp,
                'test_type': test_type,
                'test_id': result.test_id,
                'input': result.input_text,
                'expected': str(result.expected),
                'predicted': str(result.predicted),
                'correct': result.correct,
                'latency_ms': result.latency_ms,
                'error': result.error if hasattr(result, 'error') else None
            }
            
            # Add type-specific fields
            if test_type == 'finalizer' and isinstance(result, FinalizerResult):
                row['response_quality'] = result.response_quality
                row['contains_expected_keywords'] = result.contains_expected_keywords
            
            if test_type == 'e2e' and isinstance(result, E2EResult):
                row['router_correct'] = result.router_correct
                row['planner_correct'] = result.planner_correct
                row['finalizer_quality'] = result.finalizer_quality
                row['pipeline_stage_reached'] = result.pipeline_stage_reached
            
            unified_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(unified_data)
    
    # Save unified CSV
    csv_file = output_path / f"ALL_METRICS_{model_safe}_{timestamp}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    print(f"\n💾 Unified metrics saved to: {csv_file}")
    print(f"   Total records: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    
    # Also save summary stats
    summary_stats = {
        'model': model_name,
        'timestamp': timestamp,
        'total_tests': len(df),
        'by_type': df.groupby('test_type').size().to_dict(),
        'overall_accuracy': df['correct'].mean(),
        'by_type_accuracy': df.groupby('test_type')['correct'].mean().to_dict(),
        'avg_latency_ms': df['latency_ms'].mean()
    }
    
    summary_file = output_path / f"SUMMARY_{model_safe}_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    print(f"💾 Summary saved to: {summary_file}")
    
    return csv_file, summary_file


def main():
    parser = argparse.ArgumentParser(description="Complete Pipeline Benchmark")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--quantization", type=str, default="int4", choices=["int4", "int8", "fp16"])
    parser.add_argument("--dataset", type=str, default="../datasets/benchmark_dataset.json")
    parser.add_argument("--output-dir", type=str, default="../results")
    parser.add_argument("--tasks", type=str, default="all", 
                       choices=["router", "planner", "finalizer", "e2e", "all"])
    
    args = parser.parse_args()
    
    # Load dataset
    print(f"📂 Loading dataset from {args.dataset}...")
    with open(args.dataset, 'r') as f:
        test_data = json.load(f)
    
    print(f"  Router: {len(test_data['router_tests'])} tests")
    print(f"  Planner: {len(test_data['planner_tests'])} tests")
    print(f"  Finalizer: {len(test_data.get('finalizer_tests', []))} tests")
    print(f"  E2E: {len(test_data['e2e_tests'])} tests")
    
    # Initialize benchmarker
    benchmarker = CompleteBenchmarker(
        model_name=args.model,
        quantization=args.quantization
    )
    
    # Store all results
    all_results = {}
    all_summaries = {}
    
    #Run benchmarks
    if args.tasks in ["router", "all"]:
        router_results, router_summary = benchmarker.benchmark_router(test_data['router_tests'])
        all_results['router'] = router_results
        all_summaries['router'] = router_summary
        benchmarker.save_results(router_summary, args.output_dir)
    
    if args.tasks in ["planner", "all"]:
        planner_results, planner_summary = benchmarker.benchmark_planner(test_data['planner_tests'])
        all_results['planner'] = planner_results
        all_summaries['planner'] = planner_summary
        benchmarker.save_results(planner_summary, args.output_dir)
    
    if args.tasks in ["finalizer", "all"] and 'finalizer_tests' in test_data:
        finalizer_results, finalizer_summary = benchmarker.benchmark_finalizer(test_data['finalizer_tests'])
        all_results['finalizer'] = finalizer_results
        all_summaries['finalizer'] = finalizer_summary
    
    if args.tasks in ["e2e", "all"]:
        e2e_results, e2e_summary = benchmarker.benchmark_e2e(test_data['e2e_tests'])
        all_results['e2e'] = e2e_results
        all_summaries['e2e'] = e2e_summary
    
    # Export unified CSV
    if all_results:
        csv_file, summary_file = export_unified_csv(all_results, args.model, args.output_dir)
    
    # Print final summary
    print("\n" + "="*80)
    print("🎯 COMPLETE BENCHMARK SUMMARY")
    print("="*80)
    print(f"Model: {args.model}")
    for task, summary in all_summaries.items():
        print(f"\n{task.upper()}:")
        print(f"  Accuracy: {summary.accuracy:.2%} ({summary.correct}/{summary.total_tests})")
        print(f"  Avg Latency: {summary.avg_latency_ms:.0f}ms")
    
    print(f"\n✅ All results exported to: {csv_file}")
    print("\n Done!")


if __name__ == "__main__":
    main()
