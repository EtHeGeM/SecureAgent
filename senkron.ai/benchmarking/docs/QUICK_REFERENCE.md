# 🎯 BENCHMARKING QUICK REFERENCE

**One command to rule them all** 🚀

---

## ⚡ **FASTEST START**

```bash
cd /home/eren/Belgeler/senkron.ai/notebooks

# Run everything
python benchmark_complete.py --model "Qwen/Qwen2.5-7B-Instruct" --tasks all
```

**Output**: `benchmark_results/ALL_METRICS_*.csv` (55 tests in 1 file)

---

## 📊 **WHAT GETS TESTED**

| Test Type | Count | What It Tests | Time |
|-----------|-------|---------------|------|
| **Router** | 25 | Intent classification | ~5-8 min |
| **Planner** | 15 | Tool selection | ~5-8 min |
| **Finalizer** | 5 | Response generation | ~2-3 min |
| **E2E** | 10 | Full pipeline | ~8-12 min |
| **TOTAL** | **55** | Complete system | **20-30 min** |

---

## 📁 **KEY FILES**

| File | Purpose | Use When |
|------|---------|----------|
| `benchmark_complete.py` | **MAIN SCRIPT** | Full benchmark run |
| `benchmark_dataset.json` | Test cases (55 total) | Review/edit tests |
| `ALL_METRICS_*.csv` | **ALL RESULTS** | Analysis & comparison |
| `BENCHMARK_FINAL.md` | Complete documentation | Learn system |
| `analyze_results.py` | Compare models | After multiple runs |

---

## 🚀 **COMMON COMMANDS**

### **1. Full Benchmark**
```bash
python benchmark_complete.py --model "Qwen/Qwen2.5-7B-Instruct" --tasks all
```

### **2. Router Only (Fast)**
```bash
python benchmark_complete.py --model "Qwen/Qwen2.5-7B-Instruct" --tasks router
```

### **3. Different Quantization**
```bash
python benchmark_complete.py --model "Qwen/Qwen2.5-7B-Instruct" --quantization int8
```

### **4. Compare 3 Models**
```bash
for MODEL in "Qwen/Qwen2.5-7B-Instruct" \
             "meta-llama/Llama-3.1-8B-Instruct" \
             "mistralai/Mistral-7B-Instruct-v0.3"
do
    python benchmark_complete.py --model "$MODEL" --tasks all
done
```

### **5. Analyze Results**
```bash
python analyze_results.py --results-dir benchmark_results --plot
```

---

## 📊 **READING RESULTS**

### **Quick Python Analysis**:

```python
import pandas as pd

# Load results
df = pd.read_csv('benchmark_results/ALL_METRICS_Qwen_2.5-7B_*.csv')

# Overall accuracy
print(f"Accuracy: {df['correct'].mean():.2%}")

# By type
print(df.groupby('test_type')['correct'].mean())

# Failures
print(df[~df['correct']][['test_type', 'test_id', 'input']])
```

---

## 🎯 **TARGET METRICS**

| Metric | Target | Your Result |
|--------|--------|-------------|
| Router Accuracy | ≥85% | ___ % |
| Planner Accuracy | ≥75% | ___ % |
| Finalizer Quality | ≥0.80 | ___ |
| E2E Success | ≥80% | ___ % |
| Avg Latency | <1500ms | ___ ms |

---

## 🔥 **WORKFLOW**

```
1. Run benchmark ──► benchmark_complete.py --tasks all
                     (20-30 min)

2. Check CSV ─────► benchmark_results/ALL_METRICS_*.csv
                     (55 rows, 1 per test)

3. Analyze ───────► Python/Excel or analyze_results.py

4. Improve ──────► Fix prompts / Try new model

5. Repeat ───────► Compare results
```

---

## 💡 **TIPS**

### **If OOM (Out of Memory)**:
```bash
# Use smaller model
--model "Qwen/Qwen2.5-3B-Instruct"

# Or lighter quantization
--quantization int4
```

### **If Too Slow**:
```bash
# Test just router first
--tasks router

# Then add others one by one
--tasks planner
--tasks finalizer
--tasks e2e
```

### **For Quick Iteration**:
```bash
# Edit benchmark_dataset.json
# Reduce test counts for faster feedback
# Then run full suite before final decision
```

---

## 📞 **HELP**

### **View Full Docs**:
```bash
cat BENCHMARK_FINAL.md
```

### **View Test Cases**:
```bash
cat benchmark_dataset.json | jq '.router_tests'
```

### **Check Script Options**:
```bash
python benchmark_complete.py --help
```

---

## ✅ **CHECKLIST**

- [ ] Run baseline model (Qwen2.5-7B)
- [ ] Check `ALL_METRICS_*.csv` exists
- [ ] Verify >50 rows in CSV
- [ ] Overall accuracy calculated
- [ ] Top errors identified
- [ ] Decision: good enough or try another model?

---

**Last Updated**: 10 Şubat 2026  
**Status**: Production Ready ✅
