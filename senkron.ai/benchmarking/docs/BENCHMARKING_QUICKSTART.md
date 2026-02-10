# 🎯 Model Benchmarking Guide

**Son Güncelleme**: 10 Şubat 2026

Model benchmarking için hızlı başlangıç rehberi.

---

## 📋 Neler Var?

### 1. **Dataset** (`benchmark_dataset.json`)
- 15 Router test case
- 10 Planner test case
- 5 End-to-end test case

### 2. **Benchmark Runner** (`benchmark_runner.py`)
- CLI tool for running benchmarks
- Supports multiple models and quantization methods
- Generates detailed results (JSON + CSV)

### 3. **Interactive Notebook** (`model_benchmark.ipynb`)
- Jupyter/Colab friendly
- Step-by-step benchmarking
- Visualization included

### 4. **Results Analyzer** (`analyze_results.py`)
- Compare multiple model results
- Generate reports and plots
- Identify best models

---

## 🚀 Hızlı Başlangıç

### Yöntem 1: Jupyter Notebook (Önerilen)

```bash
# Colab'da notebook'u aç
notebooks/model_benchmark.ipynb

# Veya local:
jupyter notebook model_benchmark.ipynb
```

**Adımlar**:
1. Cell 1-2: Dependencies yükle
2. Cell 3: Dataset yükle
3. Cell 4: Benchmarker class tanımla
4. Cell 5: Modeli seç ve yükle
5. Cell 6: Benchmark çalıştır
6. Cell 7-8: Sonuçları analiz et

---

### Yöntem 2: CLI Script

```bash
# Tek bir model test et
python benchmark_runner.py \
  --model "Qwen/Qwen2.5-7B-Instruct" \
  --task router \
  --quantization int4

# Tüm taskları çalıştır
python benchmark_runner.py \
  --model "Qwen/Qwen2.5-7B-Instruct" \
  --task all \
  --quantization int4

# Farklı model dene
python benchmark_runner.py \
  --model "meta-llama/Llama-3.1-8B-Instruct" \
  --task router \
  --quantization int4
```

**Sonuçlar**: `benchmark_results/` klasörüne kaydedilir.

---

### Yöntem 3: Sonuçları Analiz Et

```bash
# Tüm sonuçları karşılaştır
python analyze_results.py \
  --results-dir benchmark_results \
  --output benchmark_report.md \
  --plot

# Sadece özet göster
python analyze_results.py --results-dir benchmark_results
```

**Çıktılar**:
- `benchmark_report.md` - Markdown rapor
- `accuracy_comparison.png` - Accuracy grafiği
- `latency_vs_accuracy.png` - Trade-off grafiği

---

## 📊 Test Edilecek Modeller

### Tier 1: Open-Source (3-10B parameters)

| Model | Size | Türkçe Desteği | Tool-Calling |
|-------|------|----------------|--------------|
| **Qwen2.5-7B-Instruct** | 7B | ✅ İyi | ✅ İyi |
| **Llama-3.1-8B-Instruct** | 8B | ⚠️ Orta | ✅ İyi |
| **Mistral-7B-Instruct-v0.3** | 7B | ⚠️ Orta | ✅✅ Mükemmel |
| **Gemma-2-9B-IT** | 9B | ⚠️ Orta | ✅ İyi |

### Tier 2: Larger Models (13B+)

| Model | Size | Türkçe Desteği | Tool-Calling |
|-------|------|----------------|--------------|
| **Qwen2.5-14B-Instruct** | 14B | ✅ İyi | ✅ İyi |
| **Llama-3.1-70B-Instruct** | 70B | ⚠️ Orta | ✅✅ Mükemmel |

### Tier 3: Commercial (Baseline üst sınır)

- GPT-4 Turbo
- Claude 3.5 Sonnet
- Gemini 1.5 Pro

---

## 🎯 Benchmark Metrikleri

### Router Benchmark
- **Accuracy**: Intent classification doğruluğu (Hedef: >95%)
- **F1-Score**: Dengeli performans metriği
- **Confusion Matrix**: Hangi intentler karışıyor?
- **Latency**: Ortalama yanıt süresi (Hedef: <500ms)

### Planner Benchmark
- **Tool Selection Accuracy**: Doğru araçları seçme (Hedef: >90%)
- **Tool Sequence Accuracy**: Doğru sıralama
- **Hallucination Rate**: Olmayan araç uydurma (Hedef: <1%)
- **Latency**: Plan oluşturma süresi (Hedef: <800ms)

---

## 📅 Haftalık Plan

### Hafta 1 (10-16 Şubat) - ✅ BU HAFTA

**Amaç**: Baseline modelleri test et

- [ ] **Pazartesi**: Qwen2.5-7B benchmark (Router + Planner)
- [ ] **Salı**: Llama-3.1-8B benchmark
- [ ] **Çarşamba**: Mistral-7B benchmark
- [ ] **Perşembe**: Gemma-2-9B benchmark
- [ ] **Cuma**: Sonuçları analiz et, rapor oluştur
- [ ] **Hafta Sonu**: En iyi modeli seç

### Hafta 2 (17-23 Şubat)

**Amaç**: Quantization deneyleri

- [ ] En iyi modeli FP16, INT8, INT4 ile test et
- [ ] Accuracy vs Latency trade-off analizi
- [ ] Production için model seç

### Hafta 3 (24 Şubat - 2 Mart)

**Amaç**: Fine-tuning hazırlık

- [ ] Seçilen model için fine-tuning dataset hazırla
- [ ] QLoRA setup
- [ ] İlk fine-tuning denemeleri

---

## 💡 İpuçları

### Colab'da GPU Kullanımı

```python
# GPU kontrolü
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

# Runtime → Change runtime type → GPU (T4)
```

### Model Yükleme Sorunları

```python
# NumPy hatası alırsan:
!pip install --upgrade --force-reinstall numpy
# Runtime → Restart runtime

# ChromaDB hatası alırsan:
!pip uninstall -y chromadb
!pip install chromadb
# Runtime → Restart runtime

# Bitsandbytes hatası alırsan:
!pip install -U bitsandbytes>=0.46.1
# Runtime → Restart runtime
```

### Hızlı Test (Küçük Subset)

İlk testlerde zamanı hızlandırmak için:

```python
# İlk 5 test case'i kullan
test_data['router_tests'] = test_data['router_tests'][:5]
test_data['planner_tests'] = test_data['planner_tests'][:5]
```

Her şey çalışınca tam dataseti kullan.

---

## 📈 Örnek Sonuç

```
📊 Router Benchmark Results for Qwen/Qwen2.5-7B-Instruct:
  Accuracy: 93.33% (14/15)
  F1-Score: 0.925
  Avg Latency: 847ms
  Min Latency: 612ms
  Max Latency: 1203ms

❌ Errors (1 total):
  router_012:
    Input: Başım çok ağrıyor, ne yapmalıyım?
    Expected: NO_TOOL_GENERAL | Predicted: APPT_CREATE
```

---

## 🏆 Başarı Kriterleri

| Metrik | Baseline | Hedef | Excellent |
|--------|----------|-------|-----------|
| Router Accuracy | 85% | 95% | 98% |
| Router F1-Score | 0.83 | 0.93 | 0.97 |
| Planner Accuracy | 75% | 90% | 95% |
| Hallucination Rate | 5% | 1% | 0% |
| Avg Latency (GPU T4) | 1.5s | 0.8s | 0.5s |

---

## 📚 Dosya Yapısı

```
notebooks/
├── benchmark_plan.md              # Detaylı plan
├── benchmark_dataset.json         # Test dataset
├── benchmark_runner.py            # CLI runner
├── model_benchmark.ipynb          # Interactive notebook ⭐
├── analyze_results.py             # Results analyzer
├── BENCHMARKING_QUICKSTART.md     # Bu dosya
└── benchmark_results/             # Sonuçlar (oluşturulacak)
    ├── Qwen_2.5-7B_router_20260210.json
    ├── Qwen_2.5-7B_router_20260210.csv
    ├── Llama-3.1-8B_router_20260210.json
    └── ...
```

---

## ❓ Sık Sorulan Sorular

### Q: Hangi model ile başlamalıyım?

**A**: `Qwen/Qwen2.5-7B-Instruct` - Türkçe desteği iyi, boyut makul.

### Q: GPU'da out-of-memory hatası alıyorum

**A**: 
```python
# INT4 quantization kullan (daha az bellek)
QUANTIZATION = "int4"

# Veya daha küçük model dene
MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
```

### Q: Benchmark çok uzun sürüyor

**A**: İlk testlerde dataset'i küçült:
```python
test_data['router_tests'] = test_data['router_tests'][:5]
```

### Q: Hangi sonuçları seçmeliyim?

**A**: 
- Production için: **Accuracy + Speed** dengesi
- Research için: **En yüksek accuracy**
- Demo için: **En düşük latency**

---

## 🆘 Yardım

### Sorun mu yaşıyorsun?

1. `benchmark_plan.md` dosyasını oku
2. Notebook'taki "Notes" bölümüne bak
3. Error loglarını kontrol et (`benchmark_results/*.json`)

### İletişim

- **Proje sahibi**: Senkron AI Team
- **Dokümantasyon**: `/docs/development/`

---

**Başarılar! 🚀**

Bugün ilk benchmark'ı çalıştır ve sonuçları paylaş!
