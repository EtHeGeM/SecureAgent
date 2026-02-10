# 🎯 Complete Benchmarking Suite - Results Summary

**Auto-generated on each run**

## 📊 Overview

This file contains all benchmark metrics in a single place.

### What's Included:
1. **Router Metrics** - Intent classification performance
2. **Planner Metrics** - Tool selection & sequencing
3. **Finalizer Metrics** - Response generation quality
4. **End-to-End Metrics** - Full pipeline performance
5. **Combined Summary** - Overall system performance

---

## 📁 Output Files

After running benchmarks, you'll find:

```
benchmark_results/
├── ALL_METRICS_{model}_{timestamp}.csv          # ← MAIN FILE (all metrics)
├── {model}_router_{timestamp}.csv               # Router details
├── {model}_planner_{timestamp}.csv              # Planner details
├── {model}_finalizer_{timestamp}.csv            # Finalizer details
├── {model}_e2e_{timestamp}.csv                  # E2E details
└── {model}_summary_{timestamp}.json             # Complete summary
```

---

## 🔍 CSV Structure

### ALL_METRICS.csv columns:

| Column | Description |
|--------|-------------|
| `model` | Model name |
| `timestamp` | Run timestamp |
| `test_type` | router / planner / finalizer / e2e |
| `test_id` | Unique test identifier |
| `input` | User input text |
| `expected` | Expected output |
| `predicted` | Model prediction |
| `correct` | Pass/Fail boolean |
| `latency_ms` | Response time |
| `category` | Test category |
| `complexity` | simple/medium/complex |
| `error` | Error message (if any) |

---

## 📈 Key Metrics

### Targets:
- **Router Accuracy**: ≥85%
- **Planner Accuracy**: ≥75%
- **Finalizer Quality**: ≥80%
- **E2E Success Rate**: ≥80%
- **Avg Latency**: <1500ms

---

## 🚀 How to Use

### 1. Run Benchmark:
```python
# In notebook
python model_benchmark_complete.ipynb
```

### 2. Load Results:
```python
import pandas as pd

# Load unified metrics
df = pd.read_csv('benchmark_results/ALL_METRICS_Qwen_2.5-7B_20260210.csv')

# Filter by type
router_results = df[df['test_type'] == 'router']
planner_results = df[df['test_type'] == 'planner']

# Calculate accuracy
accuracy = df['correct'].mean()
print(f"Overall Accuracy: {accuracy:.2%}")
```

### 3. Compare Models:
```bash
python analyze_results.py --results-dir benchmark_results --plot
```

---

**Last Updated**: Auto-generated
