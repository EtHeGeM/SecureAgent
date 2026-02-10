# 🚀 Open Source Model Optimization Strategy

**Date**: 10 Şubat 2026  
**Focus**: Maximize performance of open-source models (Qwen, Llama, Mistral)

---

## 🎯 **OBJECTIVE**

**Goal**: Get open-source models (Qwen 2.5 7B, Llama 3.1 8B, etc.) to **>90% accuracy** on Hospital Appointment Assistant tasks

**Current Baseline** (Expected):
- Qwen 2.5 7B: 80-88% accuracy
- Llama 3.1 8B: 75-85% accuracy
- Mistral 7B: 75-82% accuracy

**Target** (After Optimization):
- 🎯 Router: **>90%** accuracy
- 🎯 Planner: **>85%** accuracy  
- 🎯 Finalizer: **>0.90** quality
- 🎯 E2E: **>85%** success rate

---

## 📋 **OPTIMIZATION ROADMAP**

```
Phase 1: Baseline              Phase 2: Prompt            Phase 3: Fine-tuning
(Week 1)                       Engineering (Week 2)       (Week 3-4)
   ↓                               ↓                           ↓
┌──────────┐                  ┌──────────┐               ┌──────────┐
│ Run full │                  │ Optimize │               │ Collect  │
│benchmark │  →  80-85%  →    │ prompts  │  →  85-90% →  │ training │
│  suite   │      accuracy    │& context │     accuracy  │   data   │
└──────────┘                  └──────────┘               └──────────┘
                                                              ↓
                                                         ┌──────────┐
                                                         │  Train   │
                                                         │   & QLoRA│  →  90-95%
                                                         │fine-tune │     accuracy
                                                         └──────────┘
```

---

## 📊 **Phase 1: BASELINE (Bugün - Bu Hafta)**

### **Action Items:**

1. ✅ **Run Full Benchmark**
   ```bash
   cd benchmarking/scripts
   
   # Qwen 2.5 7B
   python3 benchmark_complete.py \
     --model "Qwen/Qwen2.5-7B-Instruct" \
     --quantization int4 \
     --tasks all \
     --output-dir ../results
   
   # Llama 3.1 8B (if GPU available)
   python3 benchmark_complete.py \
     --model "meta-llama/Llama-3.1-8B-Instruct" \
     --quantization int4 \
     --tasks all \
     --output-dir ../results
   ```

2. ✅ **Analyze Results**
   ```python
   import pandas as pd
   
   # Load results
   df = pd.read_csv('../results/ALL_METRICS_Qwen_*.csv')
   
   # Identify weaknesses
   failures = df[~df['correct']]
   print(failures.groupby('test_type').size())
   
   # Which categories fail most?
   print(failures['input'].value_counts())
   ```

3. ✅ **Document Findings**
   - Which test types fail most? (router, planner, etc.)
   - Which categories struggle? (APPT_CREATE, DOCTOR_INFO, etc.)
   - Common error patterns?
   - Turkish language issues?

---

## 🎨 **Phase 2: PROMPT ENGINEERING (Gelecek Hafta)**

### **Strategy:**

Prompt optimization can improve accuracy by **5-10%** without any training.

### **Techniques:**

#### **1. Few-Shot Examples**

**Before** (Zero-shot):
```python
ROUTER_PROMPT = """Classify this query into ONE category: APPT_CREATE, DOCTOR_INFO, ...

User query: {user_query}

Category:"""
```

**After** (Few-shot):
```python
ROUTER_PROMPT = """Classify user queries for a hospital appointment system.

Examples:
- "Kardiyoloji randevusu istiyorum" → APPT_CREATE
- "Dr. Ayşe kaçta çalışıyor?" → DOCTOR_INFO
- "Randevumu iptal etmek istiyorum" → APPT_CANCEL

Now classify:
User query: {user_query}

Category:"""
```

**Expected Improvement**: +3-5% accuracy

---

#### **2. Chain-of-Thought (CoT)**

**Before**:
```python
prompt = "Classify: {query}\nCategory:"
```

**After**:
```python
ROUTER_PROMPT_COT = """Classify this hospital query step-by-step:

User query: {user_query}

Step 1 - What is the user asking for?
Step 2 - Which category best matches?
Step 3 - Final classification

Category:"""
```

**Expected Improvement**: +2-3% accuracy (especially for complex queries)

---

#### **3. Turkish-Specific Instructions**

**Before**:
```python
system = "You are a helpful AI assistant."
```

**After**:
```python
TURKISH_SYSTEM = """Sen Türkçe konuşan bir hastane asistanısın. 
Türkçe dilbilgisi kurallarına dikkat et:
- "randevu almak" (appointment) vs "randevu iptal etmek" (cancel)  
- "doktor hakkında bilgi" vs "doktor randevusu"
- Resmi ve kibar dil kullan."""
```

**Expected Improvement**: +2-4% for Turkish-specific nuances

---

#### **4. Structured Output Format**

**Before**:
```python
prompt = "List tools needed: {query}"
```

**After**:
```python
PLANNER_PROMPT_STRUCTURED = """Generate a plan in this EXACT format:

{{
  "reasoning": "why these steps are needed",
  "steps": [
    {{"step": 1, "tool": "doctor.search", "params": {{}}}},
    {{"step": 2, "tool": "appointment.find_slots", "params": {{}}}}
  ]
}}

Query: {user_query}
Route: {route}

Plan (JSON):"""
```

**Expected Improvement**: +5-7% for planner accuracy

---

### **Prompt Templates to Create:**

| Task | Template File | Priority |
|------|---------------|----------|
| Router (few-shot) | `prompts/router_fewshot.txt` | HIGH |
| Router (CoT) | `prompts/router_cot.txt` | MEDIUM |
| Planner (structured) | `prompts/planner_structured.txt` | HIGH |
| Finalizer (Turkish) | `prompts/finalizer_turkish.txt` | HIGH |

---

## 🔧 **Phase 3: FINE-TUNING (Hafta 3-4)**

### **When to Fine-Tune:**

Fine-tune if:
- ✅ Prompt engineering plateaus at <85%
- ✅ Specific pattern failures identified
- ✅ Domain-specific vocabulary needed
- ✅ Have 500+ labeled examples

### **Methods:**

#### **1. Full Fine-Tuning** (Not recommended - too expensive)

❌ **Cons**: 
- Requires full model (~14GB for 7B model)
- Very slow (days)
- Risk of catastrophic forgetting

---

#### **2. LoRA (Low-Rank Adaptation)** ⭐ RECOMMENDED

✅ **Pros**:
- Only train small matrices (~50MB)
- Fast (hours instead of days)
- No catastrophic forgetting
- Can switch between tasks

**Script**:
```python
from peft import LoRA, get_peft_model
from transformers import AutoModelForCausalLM

# Load base model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# Add LoRA adapters
lora_config = LoRAConfig(
    r=8,  # rank
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1
)

model = get_peft_model(model, lora_config)

# Only 0.5% of parameters trainable!
model.print_trainable_parameters()
# trainable params: 3.67M || all params: 7.72B || trainable%: 0.0475
```

**Expected Improvement**: +5-10% accuracy

---

#### **3. QLoRA (Quantized LoRA)** ⭐⭐ BEST FOR US

✅ **Pros**:
- All LoRA benefits
- Uses INT4 quantization
- Trains on 1x T4 GPU (16GB)
- Memory efficient (~6GB)

**Implementation**:
```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

# Quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True
)

# Load model in 4-bit
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=bnb_config,
    device_map="auto"
)

# Prepare for training
model = prepare_model_for_kbit_training(model)

# Add LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Train!
trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    max_seq_length=2048,
    ...
)
trainer.train()
```

**Memory**: ~6-8GB VRAM  
**Time**: 2-4 hours on T4  
**Cost**: ~$2-5 (Colab Pro)

**Expected Improvement**: +8-12% accuracy

---

### **Training Data Requirements:**

| Task | Min Samples | Ideal Samples | Format |
|------|-------------|---------------|--------|
| Router | 200 | 500-1000 | `{input, route}` |
| Planner | 100 | 300-500 | `{input, route, tools}` |
| Finalizer | 150 | 400-600 | `{input, route, tools, response}` |

**Total**: Need **~500-1000** labeled examples

---

### **Data Collection Strategy:**

#### **Option 1: Synthetic Data Generation** (Fast)

```python
# Use GPT-4 or Claude to generate training data

synthetic_prompt = """Generate 100 Turkish hospital appointment queries.

For each, provide:
1. User query (Turkish)
2. Intent (APPT_CREATE, DOCTOR_INFO, etc.)
3. Expected tool sequence
4. Ideal response

Format as JSON array."""

# Generate with GPT-4
synthetic_data = gpt4.generate(synthetic_prompt)
```

**Time**: 1-2 hours  
**Cost**: ~$5-10  
**Quality**: Good (85-90% accuracy)

---

#### **Option 2: Real User Data** (Better)

```python
# Collect from production logs
# Label manually or semi-automatically

# Semi-automatic labeling
def label_with_model(query):
    # Use Claude/GPT-4 to suggest label
    suggestion = claude.classify(query)
    
    # Human reviews and confirms
    confirmed = human_review(query, suggestion)
    
    return confirmed
```

**Time**: 1 week  
**Cost**: Labeling time  
**Quality**: Excellent (95%+ accuracy)

---

#### **Option 3: Hybrid** ⭐ RECOMMENDED

1. Generate 300 synthetic samples (Day 1)
2. Collect 200 real queries (Week 1)
3. Label real queries semi-automatically (Week 1)
4. **Total**: 500 samples

**Time**: 1 week  
**Cost**: ~$10  
**Quality**: Very Good (90%+)

---

## 📊 **Phase 4: EVALUATION & ITERATION**

### **After Each Optimization:**

1. **Re-run Benchmark**
   ```bash
   python3 benchmark_complete.py --model "Qwen/Qwen2.5-7B-Instruct" --tasks all
   ```

2. **Compare Results**
   ```python
   baseline_df = pd.read_csv('results/baseline_qwen.csv')
   optimized_df = pd.read_csv('results/optimized_qwen.csv')
   
   print("Accuracy Improvement:")
   print(f"Baseline: {baseline_df['correct'].mean():.2%}")
   print(f"Optimized: {optimized_df['correct'].mean():.2%}")
   print(f"Delta: +{(optimized_df['correct'].mean() - baseline_df['correct'].mean()):.2%}")
   ```

3. **Identify Remaining Issues**
   ```python
   # What still fails?
   still_failing = optimized_df[~optimized_df['correct']]
   print(still_failing[['test_id', 'input', 'expected', 'predicted']])
   ```

4. **Iterate**
   - Fix prompts
   - Add more training data for specific cases
   - Try different LoRA hyperparameters

---

## 🎯 **EXPECTED TIMELINE**

| Phase | Duration | Expected Accuracy | Next Step |
|-------|----------|-------------------|-----------|
| **Baseline** | Week 1 | 80-85% | If <80%, focus on prompts |
| **Prompt Opt** | Week 2 | 85-90% | If <85%, prepare fine-tuning |
| **Fine-tuning** | Week 3-4 | 90-95% | If >90%, deploy! |
| **Iteration** | Ongoing | 92-97% | Continuous improvement |

---

## 🛠️ **TOOLS & INFRASTRUCTURE**

### **Required:**

1. **GPU Access**
   - Option A: Colab Pro ($10/month) - T4 GPU
   - Option B: RunPod (~$0.30/hour) - RTX 4090
   - Option C: Local GPU (if available)

2. **Libraries**
   ```bash
   pip install transformers peft bitsandbytes accelerate
   pip install datasets trl wandb  # for training
   ```

3. **Training Scripts**
   - Create `fine_tuning/` directory
   - Add training scripts
   - Add data preparation scripts

---

## 📁 **NEW DIRECTORY STRUCTURE**

```
benchmarking/
├── fine_tuning/              # 🆕 Fine-tuning scripts
│   ├── prepare_data.py       # Data preparation
│   ├── train_qlora.py        # QLoRA training script
│   ├── merge_adapter.py      # Merge LoRA weights
│   └── evaluate.py           # Evaluation script
├── prompts/                  # 🆕 Optimized prompts
│   ├── router_fewshot.txt
│   ├── router_cot.txt
│   ├── planner_structured.txt
│   └── finalizer_turkish.txt
├── training_data/            # 🆕 Training datasets
│   ├── router_train.jsonl
│   ├── planner_train.jsonl
│   └── finalizer_train.jsonl
└── models/                   # 🆕 Fine-tuned models
    ├── qwen-router-lora/
    ├── qwen-planner-lora/
    └── qwen-finalizer-lora/
```

---

## ✅ **ACTION PLAN (WHEN YOU SHARE BASELINE)**

When you share baseline results:

### **Step 1: Analyze (30 min)**
```python
# I'll create analysis script
python analyze_baseline.py --results baseline_results.csv

# Expected output:
# - Overall accuracy by task
# - Failure patterns
# - Error categories
# - Recommendations
```

### **Step 2: Prioritize (15 min)**
Based on results:
- If accuracy >85%: Focus on edge cases
- If accuracy 75-85%: Prompt engineering
- If accuracy <75%: Fine-tuning needed

### **Step 3: Execute (1-2 weeks)**
Create optimized prompts OR prepare fine-tuning

### **Step 4: Validate (1 day)**
Re-run benchmark with improvements

---

## 🎯 **SUCCESS CRITERIA**

| Metric | Baseline Target | Optimized Target | Final Goal |
|--------|----------------|------------------|------------|
| Router Accuracy | 80% | 88% | **>90%** |
| Planner Accuracy | 75% | 83% | **>85%** |
| Finalizer Quality | 0.75 | 0.88 | **>0.90** |
| E2E Success | 70% | 82% | **>85%** |
| Avg Latency | <1500ms | <1200ms | **<1000ms** |

---

## 📞 **NEXT STEPS**

### **Şimdi Yapılacaklar:**

1. ✅ Baseline benchmark'ı çalıştır (your turn)
2. ✅ Sonuçları paylaş
3. ⏳ Analiz et (birlikte)
4. ⏳ Optimization strategy belirle (birlikte)
5. ⏳ İmprovement execute et

---

## 📚 **RESOURCES**

- **QLoRA Paper**: https://arxiv.org/abs/2305.14314
- **PEFT Library**: https://github.com/huggingface/peft
- **Turkish LLM Benchmarks**: Research papers
- **Prompt Engineering Guide**: https://www.promptingguide.ai/

---

**Status**: ✅ READY FOR BASELINE  
**Waiting For**: Your baseline benchmark results  
**Next Action**: Analyze & optimize based on results

**Başarılar ile baseline'ı paylaş! 🚀**
