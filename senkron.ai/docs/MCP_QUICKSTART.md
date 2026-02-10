# 🚀 MCP Multi-Provider Benchmarking - QUICK START

**Created**: 10 Şubat 2026  
**Status**: Ready to Use

---

## ⚡ **5-MINUTE SETUP**

### **1. Install Dependencies**

```bash
cd /home/eren/Belgeler/senkron.ai/notebooks

# Install required packages
pip install anthropic transformers accelerate bitsandbytes torch pandas
```

### **2. Set API Keys**

```bash
# Copy example .env
cp config/.env.example config/.env

# Edit and add your Anthropic API key
nano config/.env
# or
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### **3. Run First Comparison**

```bash
# Compare Anthropic Claude vs Local Qwen
python benchmark_multi_provider.py \
  --providers "anthropic,local" \
  --tasks router \
  --output-dir benchmark_results
```

**Done!** Results in `benchmark_results/MULTI_PROVIDER_RESULTS_*.csv`

---

## 📊 **USAGE EXAMPLES**

### **Example 1: Anthropic Claude Only**

```bash
python benchmark_multi_provider.py \
  --providers anthropic \
  --anthropic-model claude-3-5-sonnet-20241022 \
  --tasks router
```

**Output**: Accuracy, latency, cost for Claude on 25 router tests

---

### **Example 2: Local Model Only**

```bash
python benchmark_multi_provider.py \
  --providers local \
  --local-model "Qwen/Qwen2.5-7B-Instruct" \
  --quantization int4 \
  --tasks router
```

**Output**: Accuracy, latency for local Qwen model

---

### **Example 3: Direct Comparison (Recommended)**

```bash
python benchmark_multi_provider.py \
  --providers "anthropic,local" \
  --anthropic-model "claude-3-5-sonnet-20241022" \
  --local-model "Qwen/Qwen2.5-7B-Instruct" \
  --quantization int4 \
  --tasks router \
  --output-dir benchmark_results
```

**Output**: Side-by-side comparison CSV + markdown report

---

### **Example 4: Test Multiple Models**

```bash
# Test Claude Sonnet vs Haiku (cost comparison)
python benchmark_multi_provider.py \
  --providers anthropic \
  --anthropic-model claude-3-5-sonnet-20241022

python benchmark_multi_provider.py \
  --providers anthropic \
  --anthropic-model claude-3-haiku-20240307

# Compare results
cat benchmark_results/COMPARISON_REPORT_*.md
```

---

## 📁 **OUTPUT FILES**

After running, you get:

```
benchmark_results/
├── MULTI_PROVIDER_RESULTS_20260210_120000.csv  # Main results file
└── COMPARISON_REPORT_20260210_120000.md        # Summary report
```

### **CSV Columns**:

| Column | Description |
|--------|-------------|
| `test_id` | Test identifier (router_001, etc.) |
| `test_type` | router, planner, etc. |
| `input_text` | User query |
| `expected` | Expected output |
| `predicted` | Model prediction |
| `correct` | Pass/Fail |
| `latency_ms` | Response time |
| `provider` | anthropic, local, etc. |
| `model` | Specific model name |
| `input_tokens` | Input token count |
| `output_tokens` | Output token count |
| `cost_usd` | Cost in USD |
| `quantization` | int4/int8/fp16 (local only) |
| `error` | Error message (if any) |

---

## 📈 **ANALYZE RESULTS**

### **Quick Python Analysis**:

```python
import pandas as pd

# Load results
df = pd.read_csv('benchmark_results/MULTI_PROVIDER_RESULTS_*.csv')

# Compare providers
comparison = df.groupby('provider').agg({
    'correct': 'mean',  # Accuracy
    'latency_ms': 'mean',  # Avg latency
    'cost_usd': 'sum'  # Total cost
}).round(4)

print(comparison)
```

**Example Output**:
```
           correct  latency_ms  cost_usd
provider                                 
anthropic   0.96      450.5     0.0245
local       0.80     1320.2     0.0000
```

---

## 💰 **COST ESTIMATES**

### **Router Benchmark (25 tests)**:

| Provider | Model | Estimated Cost |
|----------|-------|----------------|
| Anthropic | Claude 3.5 Sonnet | ~$0.02-0.05 |
| Anthropic | Claude 3 Haiku | ~$0.002-0.01 |
| OpenAI | GPT-4 Turbo | ~$0.08-0.15 |
| OpenAI | GPT-3.5 Turbo | ~$0.003-0.008 |
| Local | Any model | $0.00 (free) |

### **Full Benchmark (55 tests)**:

| Provider | Model | Estimated Cost |
|----------|-------|----------------|
| Anthropic | Claude 3.5 Sonnet | ~$0.05-0.12 |
| Anthropic | Claude 3 Haiku | ~$0.005-0.02 |
| Local | Any model | $0.00 |

**Note**: Actual costs depend on response length

---

## 🎯 **PROVIDER COMPARISON**

### **Anthropic Claude**:
- ✅ **Pros**: High accuracy, fast, reliable
- ❌ **Cons**: Costs money, requires API key
- 💰 **Cost**: $3-15 per 1M tokens
- **Best For**: Production, high-quality responses

### **Local Models (Qwen, Llama, Mistral)**:
- ✅ **Pros**: Free, private, customizable
- ❌ **Cons**: Slower, requires GPU, setup complexity
- 💰 **Cost**: $0 (GPU infrastructure not included)
- **Best For**: Development, cost-sensitive, privacy

---

## 🔧 **TROUBLESHOOTING**

### **"Anthropic API key not found"**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### **"Out of Memory" (Local Models)**
```bash
# Use lighter quantization
--quantization int4

# Or smaller model
--local-model "Qwen/Qwen2.5-3B-Instruct"
```

### **"Module not found: anthropic"**
```bash
pip install anthropic
```

### **Slow Local Model**
- Check GPU availability: `nvidia-smi`
- Use INT4 quantization
- Reduce max_tokens

---

## 📚 **NEXT STEPS**

1. ✅ **Run first comparison** (Anthropic vs Local)
2. ✅ **Analyze results** (Which is better for your use case?)
3. ✅ **Cost-benefit analysis** (Accuracy vs Cost)
4. ✅ **Model selection** (Choose best model for production)
5. ✅ **Fine-tuning** (Improve local model if needed)

---

## 🆘 **NEED HELP?**

### **View Full Documentation**:
```bash
cat MCP_BACKEND_REQUIREMENTS.md
```

### **Test Single Provider**:
```python
# Python script test
from mcp_server.providers import create_anthropic_provider

provider = create_anthropic_provider(model_name="claude-3-5-sonnet-20241022")
response = provider.generate("Kardiyoloji randevu istiyorum")
print(f"Response: {response.text}")
print(f"Cost: ${response.cost_usd:.6f}")
print(f"Latency: {response.latency_ms:.0f}ms")
```

---

## ✅ **CHECKLIST**

- [ ] Dependencies installed (`pip install anthropic transformers ...`)
- [ ] API key set (`export ANTHROPIC_API_KEY=...`)
- [ ] First benchmark run (`python benchmark_multi_provider.py ...`)
- [ ] Results CSV exists (`ls benchmark_results/`)
- [ ] Comparison report generated
- [ ] Cost calculated (<$0.10 for router tests)
- [ ] Model selected for next phase

---

**Ready to run!** 🚀

Start with:
```bash
python benchmark_multi_provider.py --providers "anthropic,local" --tasks router
```
