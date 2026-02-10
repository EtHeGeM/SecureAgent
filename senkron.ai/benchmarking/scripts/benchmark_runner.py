"""
Model Benchmarking Script for Hospital Appointment Assistant
Evaluates different LLM models on Router and Planner tasks

Usage:
    python benchmark_runner.py --model "Qwen/Qwen2.5-7B-Instruct" --task router
    python benchmark_runner.py --model "meta-llama/Llama-3.1-8B-Instruct" --task planner
    python benchmark_runner.py --model "Qwen/Qwen2.5-7B-Instruct" --task all
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import argparse

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import pandas as pd


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    test_id: str
    input_text: str
    expected: Any
    predicted: Any
    correct: bool
    latency_ms: float
    error: str = None


@dataclass
class ModelBenchmarkSummary:
    """Summary of benchmark results for a model"""
    model_name: str
    task: str  # router, planner, e2e
    total_tests: int
    correct: int
    accuracy: float
    avg_latency_ms: float
    total_time_s: float
    f1_score: float = None
    error_rate: float = None
    details: List[BenchmarkResult] = None


class ModelBenchmarker:
    """Benchmark runner for LLM models"""
    
    def __init__(self, model_name: str, quantization: str = "int4", device: str = "auto"):
        """
        Initialize benchmarker with a specific model
        
        Args:
            model_name: HuggingFace model identifier
            quantization: int4, int8, or fp16
            device: cuda, cpu, or auto
        """
        self.model_name = model_name
        self.quantization = quantization
        self.device = device
        
        print(f"Loading model: {model_name} with {quantization} quantization...")
        self.tokenizer, self.model = self._load_model()
        print("✅ Model loaded successfully!")
    
    def _load_model(self):
        """Load model with specified quantization"""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        
        if self.quantization == "int4":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map=self.device,
                trust_remote_code=True
            )
        elif self.quantization == "int8":
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map=self.device,
                trust_remote_code=True
            )
        else:  # fp16
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map=self.device,
                trust_remote_code=True
            )
        
        return tokenizer, model
    
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text from model"""
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant for a hospital appointment system."},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,  # Deterministic for benchmarking
                temperature=0.1,
                top_p=0.95
            )
        
        generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|im_start|>assistant" in generated:
            response = generated.split("<|im_start|>assistant")[-1].strip()
        elif "assistant\n" in generated:
            response = generated.split("assistant\n")[-1].strip()
        else:
            response = generated
        
        return response
    
    def benchmark_router(self, test_data: List[Dict]) -> ModelBenchmarkSummary:
        """
        Benchmark router intent classification
        
        Args:
            test_data: List of test cases with 'input' and 'expected_route'
        
        Returns:
            ModelBenchmarkSummary with results
        """
        print(f"\n🧪 Running Router Benchmark ({len(test_data)} tests)...")
        
        ROUTER_PROMPT_TEMPLATE = """You are an intent classifier for a hospital appointment system.

Classify the user's query into ONE of these categories:
- APPT_CREATE: Creating a new appointment
- DOCTOR_INFO: Asking about doctors or their availability
- APPT_CANCEL: Canceling or rescheduling an appointment
- KB_INFO: General hospital information (parking, visiting hours, etc.)
- APPT_INFO: Checking existing appointment status
- NO_TOOL_GENERAL: Greetings, gratitude, or medical advice requests (blocked)

User query: {user_query}

Respond with ONLY the category name, nothing else."""

        results = []
        start_time = time.time()
        
        for test in test_data:
            prompt = ROUTER_PROMPT_TEMPLATE.format(user_query=test['input'])
            
            test_start = time.time()
            try:
                response = self.generate(prompt, max_tokens=50)
                latency_ms = (time.time() - test_start) * 1000
                
                # Extract route from response
                predicted_route = response.strip().split('\n')[0].strip()
                
                # Match to valid routes
                valid_routes = ["APPT_CREATE", "DOCTOR_INFO", "APPT_CANCEL", "KB_INFO", "APPT_INFO", "NO_TOOL_GENERAL"]
                
                # Find best match
                if predicted_route in valid_routes:
                    final_prediction = predicted_route
                else:
                    # Try to extract from text
                    for route in valid_routes:
                        if route in response.upper():
                            final_prediction = route
                            break
                    else:
                        final_prediction = "UNKNOWN"
                
                correct = (final_prediction == test['expected_route'])
                
                result = BenchmarkResult(
                    test_id=test['test_id'],
                    input_text=test['input'],
                    expected=test['expected_route'],
                    predicted=final_prediction,
                    correct=correct,
                    latency_ms=latency_ms
                )
                
            except Exception as e:
                result = BenchmarkResult(
                    test_id=test['test_id'],
                    input_text=test['input'],
                    expected=test['expected_route'],
                    predicted="ERROR",
                    correct=False,
                    latency_ms=0,
                    error=str(e)
                )
            
            results.append(result)
            print(f"  [{test['test_id']}] {'✅' if result.correct else '❌'} {result.latency_ms:.0f}ms")
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        y_true = [r.expected for r in results]
        y_pred = [r.predicted for r in results]
        
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        correct_count = sum(1 for r in results if r.correct)
        avg_latency = sum(r.latency_ms for r in results) / len(results)
        
        summary = ModelBenchmarkSummary(
            model_name=self.model_name,
            task="router",
            total_tests=len(results),
            correct=correct_count,
            accuracy=accuracy,
            avg_latency_ms=avg_latency,
            total_time_s=total_time,
            f1_score=f1,
            details=results
        )
        
        print(f"\n📊 Router Results:")
        print(f"  Accuracy: {accuracy:.2%}")
        print(f"  F1-Score: {f1:.3f}")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  Total Time: {total_time:.1f}s")
        
        return summary
    
    def benchmark_planner(self, test_data: List[Dict]) -> ModelBenchmarkSummary:
        """
        Benchmark planner tool selection
        
        Args:
            test_data: List of test cases with 'input' and 'expected_tools'
        
        Returns:
            ModelBenchmarkSummary with results
        """
        print(f"\n🧪 Running Planner Benchmark ({len(test_data)} tests)...")
        
        PLANNER_PROMPT_TEMPLATE = """You are a task planner for a hospital appointment system.

Available tools:
- kb.search: Search knowledge base for general hospital information
- doctor.search: Search for doctors by name or specialty
- doctor.profile: Get detailed doctor profile
- appointment.find_slots: Find available appointment slots for a doctor
- appointment.create: Create a new appointment
- appointment.info: Get information about an existing appointment
- appointment.cancel: Cancel an appointment

User query: {user_query}
Route: {route}

Generate a step-by-step plan. For each step, specify:
1. step_id (integer)
2. tool (exact tool name from the list above)
3. reasoning (why this step is needed)

Respond in JSON format:
{{
  "steps": [
    {{"step_id": 1, "tool": "doctor.search", "reasoning": "..."}},
    {{"step_id": 2, "tool": "appointment.find_slots", "reasoning": "..."}}
  ]
}}"""

        results = []
        start_time = time.time()
        
        for test in test_data:
            prompt = PLANNER_PROMPT_TEMPLATE.format(
                user_query=test['input'],
                route=test['route']
            )
            
            test_start = time.time()
            try:
                response = self.generate(prompt, max_tokens=512)
                latency_ms = (time.time() - test_start) * 1000
                
                # Extract JSON from response
                try:
                    # Find JSON in response
                    if "```json" in response:
                        json_str = response.split("```json")[1].split("```")[0].strip()
                    elif "{" in response and "}" in response:
                        start_idx = response.find("{")
                        end_idx = response.rfind("}") + 1
                        json_str = response[start_idx:end_idx]
                    else:
                        json_str = response
                    
                    plan = json.loads(json_str)
                    predicted_tools = [step['tool'] for step in plan.get('steps', [])]
                except:
                    predicted_tools = []
                
                # Check if tools match (order matters for sequence, set for selection)
                tools_match = (predicted_tools == test['expected_tools'])
                tools_set_match = (set(predicted_tools) == set(test['expected_tools']))
                
                # Consider correct if either exact match or set match
                correct = tools_match or tools_set_match
                
                result = BenchmarkResult(
                    test_id=test['test_id'],
                    input_text=test['input'],
                    expected=test['expected_tools'],
                    predicted=predicted_tools,
                    correct=correct,
                    latency_ms=latency_ms
                )
                
            except Exception as e:
                result = BenchmarkResult(
                    test_id=test['test_id'],
                    input_text=test['input'],
                    expected=test['expected_tools'],
                    predicted=[],
                    correct=False,
                    latency_ms=0,
                    error=str(e)
                )
            
            results.append(result)
            print(f"  [{test['test_id']}] {'✅' if result.correct else '❌'} {result.latency_ms:.0f}ms")
        
        total_time = time.time() - start_time
        
        correct_count = sum(1 for r in results if r.correct)
        accuracy = correct_count / len(results)
        avg_latency = sum(r.latency_ms for r in results) / len(results)
        
        summary = ModelBenchmarkSummary(
            model_name=self.model_name,
            task="planner",
            total_tests=len(results),
            correct=correct_count,
            accuracy=accuracy,
            avg_latency_ms=avg_latency,
            total_time_s=total_time,
            details=results
        )
        
        print(f"\n📊 Planner Results:")
        print(f"  Accuracy: {accuracy:.2%}")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  Total Time: {total_time:.1f}s")
        
        return summary
    
    def save_results(self, summary: ModelBenchmarkSummary, output_dir: str = "../results"):
        """Save benchmark results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save summary
        summary_dict = asdict(summary)
        summary_dict['details'] = [asdict(r) for r in summary.details]
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        model_safe_name = self.model_name.replace("/", "_")
        filename = f"{model_safe_name}_{summary.task}_{timestamp}.json"
        
        with open(output_path / filename, 'w', encoding='utf-8') as f:
            json.dump(summary_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path / filename}")
        
        # Save CSV for easy analysis
        df = pd.DataFrame([asdict(r) for r in summary.details])
        csv_filename = filename.replace('.json', '.csv')
        df.to_csv(output_path / csv_filename, index=False)
        print(f"💾 CSV saved to: {output_path / csv_filename}")


def load_test_data(data_file: str = "../datasets/benchmark_dataset.json") -> Dict:
    """Load test dataset"""
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Benchmark LLM models for hospital assistant")
    parser.add_argument("--model", type=str, required=True, help="HuggingFace model name")
    parser.add_argument("--task", type=str, choices=["router", "planner", "all"], default="all")
    parser.add_argument("--quantization", type=str, choices=["int4", "int8", "fp16"], default="int4")
    parser.add_argument("--dataset", type=str, default="../datasets/benchmark_dataset.json")
    parser.add_argument("--output-dir", type=str, default="../results")
    
    args = parser.parse_args()
    
    # Load test data
    print(f"📂 Loading test data from {args.dataset}...")
    test_data = load_test_data(args.dataset)
    
    # Initialize benchmarker
    benchmarker = ModelBenchmarker(
        model_name=args.model,
        quantization=args.quantization
    )
    
    # Run benchmarks
    if args.task in ["router", "all"]:
        router_summary = benchmarker.benchmark_router(test_data['router_tests'])
        benchmarker.save_results(router_summary, args.output_dir)
    
    if args.task in ["planner", "all"]:
        planner_summary = benchmarker.benchmark_planner(test_data['planner_tests'])
        benchmarker.save_results(planner_summary, args.output_dir)
    
    print("\n✅ Benchmarking complete!")


if __name__ == "__main__":
    main()
