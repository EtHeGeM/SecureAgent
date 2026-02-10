# 📁 Senkron.AI Project Structure

**Reorganized**: 10 Şubat 2026  
**Organized & Professional Structure**

---

## 🗂️ **Directory Overview**

```
senkron.ai/
├── 📓 notebooks/              # Jupyter notebooks only
├── 🔬 benchmarking/           # Model benchmarking system
├── 🔌 mcp_backend/            # MCP server & providers
├── 📚 docs/                   # Documentation
├── ⚙️  config/                # Configuration files
├── 🛠️  tools/                 # Helper tools & scripts
├── 📊 assets/                 # Static assets
├── 📝 logs/                   # Application logs
└── 🎯 ornek-proje/            # Example projects
```

---

## 📓 **notebooks/**

**Purpose**: Jupyter notebooks for interactive development and demos

```
notebooks/
├── hospital_appointment_assistant_baseline.ipynb   # Baseline implementation
├── hospital_appointment_assistant_mvp.ipynb        # MVP version
├── Hospital_Assistant_Gradio_Demo.ipynb            # Gradio demo
├── model_benchmark.ipynb                           # Interactive benchmarking
└── README.md                                       # Notebook documentation
```

**Use for**: 
- Interactive development
- Demos and presentations
- Exploratory data analysis

---

## 🔬 **benchmarking/**

**Purpose**: Complete model benchmarking system

```
benchmarking/
├── scripts/                   # Benchmark scripts
│   ├── benchmark_runner.py           # CLI benchmark tool
│   ├── benchmark_complete.py         # Full E2E benchmark
│   ├── benchmark_multi_provider.py   # Multi-provider comparison
│   └── analyze_results.py            # Results analysis
├── datasets/                  # Test datasets
│   └── benchmark_dataset.json        # 55 test cases
├── results/                   # Benchmark outputs (gitignored)
│   ├── *.csv                         # Result CSVs
│   └── *.json                        # Summary JSONs
└── docs/                      # Benchmarking documentation
    ├── benchmark_plan.md
    ├── BENCHMARKING_QUICKSTART.md
    ├── BENCHMARK_COMPLETE.md
    ├── BENCHMARK_FINAL.md
    ├── BENCHMARK_RESULTS_README.md
    └── QUICK_REFERENCE.md
```

**Key Features**:
- Router, Planner, Finalizer, E2E benchmarks
- Multi-provider support (Anthropic, Local models)
- Cost tracking & analysis
- Unified CSV export

**Quick Start**:
```bash
cd benchmarking/scripts
python benchmark_multi_provider.py --providers "anthropic,local" --tasks router
```

---

## 🔌 **mcp_backend/**

**Purpose**: MCP server implementation with multi-provider support

```
mcp_backend/
└── mcp_server/
    ├── __init__.py
    └── providers/
        ├── __init__.py
        ├── base_provider.py           # Abstract base
        ├── anthropic_provider.py      # Claude API
        └── huggingface_provider.py    # Local models
```

**Supported Providers**:
- ✅ Anthropic (Claude 3.5 Sonnet, 3 Opus, 3 Haiku)
- ✅ HuggingFace (Qwen, Llama, Mistral, Gemma)
- 🔜 OpenAI (GPT-4, GPT-3.5)
- 🔜 Google (Gemini)

**Usage**:
```python
from mcp_backend.mcp_server.providers import create_anthropic_provider

provider = create_anthropic_provider(model_name="claude-3-5-sonnet-20241022")
response = provider.generate("Kardiyoloji randevu istiyorum")
```

---

## 📚 **docs/**

**Purpose**: All project documentation

```
docs/
├── MCP_BACKEND_REQUIREMENTS.md     # MCP architecture
├── MCP_QUICKSTART.md               # MCP quick start
├── MCP_COMPLETE.md                 # MCP summary
├── DOCUMENTATION_INDEX.md          # Docs index
├── CHANGELOG.md                    # Version history
├── FILE_REORGANIZATION_REPORT.md   # This reorganization
└── [other docs]/                   # Subdirectories
    ├── architecture/
    ├── data/
    ├── deployment/
    └── planning/
```

**Browse**: Start with `DOCUMENTATION_INDEX.md`

---

## ⚙️ **config/**

**Purpose**: Configuration files and templates

```
config/
├── .env.example               # API keys template
├── providers.json             # Provider configurations (future)
└── [app configs]              # Application configs
```

**Setup**:
```bash
cp config/.env.example config/.env
# Edit .env with your API keys
```

---

## 🛠️ **tools/**

**Purpose**: Helper scripts and utilities

```
tools/
└── [future utilities]
```

**Future additions**:
- Data preprocessing scripts
- Deployment helpers
- Testing utilities

---

## 🎯 **Quick Navigation**

### **Want to...**

| I want to... | Go to... |
|-------------|----------|
| Run benchmarks | `benchmarking/scripts/` |
| Compare models | `benchmarking/scripts/benchmark_multi_provider.py` |
| View test data | `benchmarking/datasets/benchmark_dataset.json` |
| Check results | `benchmarking/results/` |
| Use MCP providers | `mcp_backend/mcp_server/providers/` |
| Read docs | `docs/` |
| Interactive notebooks | `notebooks/` |
| Configure API keys | `config/.env.example` |

---

## 🚀 **Getting Started**

### **1. Model Benchmarking**

```bash
# Navigate to benchmarking
cd benchmarking/scripts

# Run quick benchmark
python benchmark_multi_provider.py \
  --providers "anthropic,local" \
  --tasks router

# View results
cat ../results/MULTI_PROVIDER_RESULTS_*.csv
```

**Documentation**: `benchmarking/docs/BENCHMARKING_QUICKSTART.md`

---

### **2. MCP Backend**

```bash
# Install dependencies
pip install anthropic transformers accelerate bitsandbytes

# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Test provider
python -c "
from mcp_backend.mcp_server.providers import create_anthropic_provider
provider = create_anthropic_provider()
print(provider.generate('Test'))
"
```

**Documentation**: `docs/MCP_QUICKSTART.md`

---

### **3. Interactive Notebooks**

```bash
# Navigate to notebooks
cd notebooks

# Start Jupyter
jupyter notebook

# Open any .ipynb file
```

---

## 📋 **Maintenance**

### **Adding New Files**

- **Notebooks** → `notebooks/`
- **Benchmark scripts** → `benchmarking/scripts/`
- **Test data** → `benchmarking/datasets/`
- **Documentation** → `docs/` or `benchmarking/docs/`
- **MCP providers** → `mcp_backend/mcp_server/providers/`
- **Config templates** → `config/`

### **Gitignore Additions**

```bash
# Already ignored
benchmarking/results/
config/.env
*.pyc
__pycache__/
logs/
```

---

## 🔄 **Migration Notes**

**From**: All files in `notebooks/`  
**To**: Organized structure  
**Date**: 10 Şubat 2026

**Changes**:
- ✅ Benchmarking tools → `benchmarking/scripts/`
- ✅ Benchmark data → `benchmarking/datasets/`
- ✅ Benchmark docs → `benchmarking/docs/`
- ✅ MCP server → `mcp_backend/`
- ✅ MCP docs → `docs/`
- ✅ Config → `config/`
- ✅ Notebooks remain → `notebooks/` (cleaned up)

**Benefits**:
- Clear separation of concerns
- Easier navigation
- Professional structure
- Scalable for growth

---

## 📞 **Help**

- **Benchmarking**: Read `benchmarking/docs/BENCHMARKING_QUICKSTART.md`
- **MCP Backend**: Read `docs/MCP_QUICKSTART.md`
- **General Docs**: Check `docs/DOCUMENTATION_INDEX.md`

---

**Last Updated**: 10 Şubat 2026  
**Structure Version**: 2.0
