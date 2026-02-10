# 🚀 Benchmarking Scripts

**Comprehensive model benchmarking tools**

---

## 📁 **Files**

| Script | Purpose | Usage |
|--------|---------|-------|
| `benchmark_runner.py` | CLI benchmark tool for router/planner | `python benchmark_runner.py --model "Qwen/..." --task router` |
| `benchmark_complete.py` | Full E2E benchmark (Router+Planner+Finalizer+E2E) | `python benchmark_complete.py --model "Qwen/..." --tasks all` |
| `benchmark_multi_provider.py` | **Multi-provider comparison** (Anthropic vs Local) | `python benchmark_multi_provider.py --providers "anthropic,local"` |
| `analyze_results.py` | Results analysis & comparison | `python analyze_results.py --results-dir ../results` |

---

## 🎯 **Quick Start**

### **1. Multi-Provider Comparison** (Recommended)

Compare Anthropic Claude vs Local Models:

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run comparison
python benchmark_multi_provider.py \
  --providers "anthropic,local" \
  --anthropic-model "claude-3-5-sonnet-20241022" \
  --local-model "Qwen/Qwen2.5-7B-Instruct" \
  --quantization int4 \
  --tasks router \
  --output-dir ../results
```

**Output**: `../results/MULTI_PROVIDER_RESULTS_*.csv`

---

### **2. Single Model Benchmark**

Test one model (local or API):

```bash
# Local model
python benchmark_runner.py \
  --model "Qwen/Qwen2.5-7B-Instruct" \
  --task router \
  --quantization int4 \
  --output-dir ../results

# Or use complete E2E
python benchmark_complete.py \
  --model "Qwen/Qwen2.5-7B-Instruct" \
  --tasks all \
  --output-dir ../results
```

---

### **3. Analyze Results**

After running benchmarks:

```bash
python analyze_results.py \
  --results-dir ../results \
  --output ../results/comparison_report.md \
  --plot
```

---

## 📊 **Expected Outputs**

All results go to `../results/`:

```
results/
├── MULTI_PROVIDER_RESULTS_20260210.csv    # Multi-provider comparison
├── COMPARISON_REPORT_20260210.md          # Summary report
├── Qwen_2.5-7B_router_20260210.csv       # Single model results
├── accuracy_comparison.png                 # Plots
└── latency_vs_accuracy.png
```

---

## 🔧 **Configuration**

### **Import Paths**

Scripts now import from parent directory:

```python
import sys
from pathlib import Path

# Add parent to path for mcp_server imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mcp_backend.mcp_server.providers import (
    create_anthropic_provider,
    create_huggingface_provider
)
```

### **Dataset Path**

Update dataset path in scripts:

```python
# OLD: "benchmark_dataset.json"
# NEW: "../datasets/benchmark_dataset.json"
```

---

## 📝 **Notes**

- **Benchmarking docs**: See `../docs/`
- **Test data**: Located in `../datasets/`
- **Results**: Auto-saved to `../results/`
- **MCP providers**: In `../../mcp_backend/mcp_server/providers/`

---

## 🆘 **Troubleshooting**

### **Import Error**

```python
# Error: ModuleNotFoundError: No module named 'mcp_backend'

# Fix: Run from scripts directory
cd /path/to/senkron.ai/benchmarking/scripts
python benchmark_multi_provider.py ...
```

### **Dataset Not Found**

```bash
# Ensure you're in scripts/ directory
pwd  # Should end with /benchmarking/scripts

# Dataset should be at ../datasets/benchmark_dataset.json
ls ../datasets/
```

---

**Quick Test**:
```bash
cd /home/eren/Belgeler/senkron.ai/benchmarking/scripts
python benchmark_multi_provider.py --help
```
