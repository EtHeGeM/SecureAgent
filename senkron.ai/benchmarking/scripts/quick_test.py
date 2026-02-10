"""
Quick Validation Test - Minimal Benchmark
Tests 5 samples to validate system works without full benchmark run

Usage:
    python quick_test.py --provider anthropic
    python quick_test.py --provider local
"""

import json
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_backend.mcp_server.providers import (
    create_anthropic_provider,
    create_huggingface_provider
)


# Quick test cases (5 samples from dataset)
QUICK_TESTS = [
    {
        "test_id": "quick_001",
        "input": "Kardiyoloji için yarın randevu istiyorum",
        "expected_route": "APPT_CREATE",
        "description": "Simple appointment request"
    },
    {
        "test_id": "quick_002",
        "input": "Dr. Ayşe Yılmaz hangi günler çalışıyor?",
        "expected_route": "DOCTOR_INFO",
        "description": "Doctor availability"
    },
    {
        "test_id": "quick_003",
        "input": "Randevumu iptal etmek istiyorum",
        "expected_route": "APPT_CANCEL",
        "description": "Cancel appointment"
    },
    {
        "test_id": "quick_004",
        "input": "Hastane kaçta açılıyor?",
        "expected_route": "KB_INFO",
        "description": "General info"
    },
    {
        "test_id": "quick_005",
        "input": "Randevu bilgisi alabilir miyim?",
        "expected_route": "APPT_INFO",
        "description": "Appointment info"
    }
]


ROUTER_PROMPT = """Classify this query into ONE category: APPT_CREATE, DOCTOR_INFO, APPT_CANCEL, KB_INFO, APPT_INFO, NO_TOOL_GENERAL

User query: {user_query}

Respond with ONLY the category name."""


def run_quick_test(provider, provider_name):
    """Run quick validation test"""
    print(f"\n🧪 Running Quick Test for {provider_name}...")
    print(f"   Testing {len(QUICK_TESTS)} samples")
    
    results = []
    start_time = time.time()
    
    for i, test in enumerate(QUICK_TESTS, 1):
        prompt = ROUTER_PROMPT.format(user_query=test['input'])
        
        try:
            test_start = time.time()
            response = provider.generate(prompt, max_tokens=50)
            latency = (time.time() - test_start) * 1000
            
            # Extract route
            predicted = response.text.strip().split('\n')[0].strip()
            valid_routes = ["APPT_CREATE", "DOCTOR_INFO", "APPT_CANCEL", "KB_INFO", "APPT_INFO", "NO_TOOL_GENERAL"]
            
            if predicted not in valid_routes:
                for route in valid_routes:
                    if route in response.text.upper():
                        predicted = route
                        break
                else:
                    predicted = "UNKNOWN"
            
            correct = (predicted == test['expected_route'])
            
            results.append({
                'test_id': test['test_id'],
                'input': test['input'],
                'expected': test['expected_route'],
                'predicted': predicted,
                'correct': correct,
                'latency_ms': latency,
                'cost_usd': response.cost_usd
            })
            
            status = "✅" if correct else "❌"
            print(f"  [{i}/{len(QUICK_TESTS)}] {status} {test['test_id']}: {latency:.0f}ms, ${response.cost_usd:.6f}")
            
        except Exception as e:
            print(f"  [{i}/{len(QUICK_TESTS)}] ❌ {test['test_id']}: ERROR - {str(e)}")
            results.append({
                'test_id': test['test_id'],
                'input': test['input'],
                'expected': test['expected_route'],
                'predicted': 'ERROR',
                'correct': False,
                'latency_ms': 0,
                'cost_usd': 0,
                'error': str(e)
            })
    
    total_time = time.time() - start_time
    
    # Calculate metrics
    correct_count = sum(1 for r in results if r['correct'])
    accuracy = correct_count / len(results)
    avg_latency = sum(r['latency_ms'] for r in results) / len(results)
    total_cost = sum(r['cost_usd'] for r in results)
    
    # Print summary
    print(f"\n📊 {provider_name} Results:")
    print(f"  Accuracy: {correct_count}/{len(results)} ({accuracy:.1%})")
    print(f"  Avg Latency: {avg_latency:.0f}ms")
    print(f"  Total Cost: ${total_cost:.6f}")
    print(f"  Total Time: {total_time:.1f}s")
    
    # Provider stats
    stats = provider.get_stats()
    print(f"\n📈 Provider Statistics:")
    print(f"  Total tokens: {stats['total_tokens']:,}")
    print(f"  Avg tokens/request: {stats['avg_input_tokens_per_request']:.0f} in + {stats['avg_output_tokens_per_request']:.0f} out")
    
    return results, accuracy, avg_latency, total_cost


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick validation test")
    parser.add_argument("--provider", type=str, choices=["anthropic", "local"], default="anthropic")
    parser.add_argument("--anthropic-model", type=str, default="claude-3-haiku-20240307")
    parser.add_argument("--local-model", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--quantization", type=str, default="int4")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 QUICK VALIDATION TEST")
    print("="*60)
    print(f"Provider: {args.provider}")
    
    # Initialize provider
    if args.provider == "anthropic":
        print(f"Model: {args.anthropic_model}")
        print("\n⏳ Initializing Anthropic provider...")
        provider = create_anthropic_provider(model_name=args.anthropic_model)
        provider_name = f"Anthropic {args.anthropic_model}"
    else:
        print(f"Model: {args.local_model}")
        print(f"Quantization: {args.quantization}")
        print("\n⏳ Loading local model (this may take 1-2 minutes)...")
        provider = create_huggingface_provider(
            model_name=args.local_model,
            quantization=args.quantization
        )
        provider_name = f"Local {args.local_model}"
    
    # Run test
    results, accuracy, avg_latency, total_cost = run_quick_test(provider, provider_name)
    
    # Final summary
    print("\n" + "="*60)
    print("✅ QUICK TEST COMPLETE")
    print("="*60)
    print(f"\n🎯 Key Metrics:")
    print(f"  ✓ Accuracy: {accuracy:.1%}")
    print(f"  ✓ Avg Latency: {avg_latency:.0f}ms")
    print(f"  ✓ Total Cost: ${total_cost:.6f}")
    
    # Comparison to targets
    print(f"\n📊 vs Target (85% accuracy, <1500ms):")
    if accuracy >= 0.85:
        print(f"  ✅ Accuracy: PASS ({accuracy:.1%} >= 85%)")
    else:
        print(f"  ❌ Accuracy: FAIL ({accuracy:.1%} < 85%)")
    
    if avg_latency <= 1500:
        print(f"  ✅ Latency: PASS ({avg_latency:.0f}ms <= 1500ms)")
    else:
        print(f"  ⚠️  Latency: WARNING ({avg_latency:.0f}ms > 1500ms)")
    
    # Save results
    output_file = f"quick_test_{args.provider}_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'provider': args.provider,
            'model': args.anthropic_model if args.provider == 'anthropic' else args.local_model,
            'accuracy': accuracy,
            'avg_latency_ms': avg_latency,
            'total_cost_usd': total_cost,
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print("\n🎉 Done!\n")


if __name__ == "__main__":
    main()
