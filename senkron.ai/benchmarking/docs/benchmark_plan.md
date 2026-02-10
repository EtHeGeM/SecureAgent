# 🎯 Model Benchmarking Plan

**Tarih**: 10 Şubat 2026  
**Amaç**: Hospital Appointment Assistant için farklı LLM modellerini karşılaştırmalı değerlendirme

---

## 📊 Benchmark Metrikleri

### 1. Router Benchmarks
- **Accuracy**: Intent classification doğruluğu
- **F1-Score**: Her route kategorisi için (APPT_CREATE, DOCTOR_INFO, etc.)
- **Latency**: Intent belirleme süresi
- **Confusion Matrix**: Hangi intentler karışıyor?

### 2. Planner Benchmarks
- **Tool Selection Accuracy**: Doğru araçları seçme oranı
- **Tool Sequence Accuracy**: Doğru sıralama oranı
- **Dependency Resolution**: Araç arası veri aktarımı doğruluğu
- **Hallucination Rate**: Olmayan araç uydurma oranı
- **Latency**: Plan oluşturma süresi

### 3. End-to-End Benchmarks
- **Success Rate**: Tüm pipeline başarı oranı
- **Average Latency**: Ortalama yanıt süresi (Router + Planner + Executor)
- **Error Rate by Type**: Hata tiplerinin dağılımı
- **Token Usage**: Ortalama token tüketimi

### 4. Model Comparison
- **Model Families**: Qwen2.5, Llama 3.1, Mistral, Gemma
- **Model Sizes**: 3B, 7B, 13B parameters
- **Quantization**: FP16, INT8, INT4
- **Cost vs Performance**: Token/$ bazında değerlendirme

---

## 🧪 Test Senaryoları

### A. Router Test Set (200 örnek)
```
- APPT_CREATE: 70 örnek (35%)
- DOCTOR_INFO: 40 örnek (20%)
- APPT_CANCEL: 30 örnek (15%)
- KB_INFO: 20 örnek (10%)
- APPT_INFO: 20 örnek (10%)
- NO_TOOL_GENERAL: 20 örnek (10%)
```

### B. Planner Test Set (150 örnek)
```
- Simple (1 tool): 50 örnek
- Medium (2-3 tools): 70 örnek
- Complex (4+ tools): 30 örnek
```

### C. End-to-End Test Set (100 örnek)
```
- Happy path: 60 örnek
- Edge cases: 25 örnek
- Error handling: 15 örnek
```

---

## 🏗️ Benchmark Altyapısı

### 1. Dataset Yapısı
```json
{
  "test_id": "router_001",
  "category": "APPT_CREATE",
  "input": "Kardiyoloji için yarın randevu istiyorum",
  "expected_output": {
    "route": "APPT_CREATE",
    "confidence": 0.95,
    "requires_tools": true
  }
}
```

### 2. Benchmark Script
```python
# notebooks/benchmark_runner.py
class Benchmarker:
    - load_test_data()
    - run_router_benchmark()
    - run_planner_benchmark()
    - run_e2e_benchmark()
    - generate_report()
```

### 3. Sonuç Formatı
```json
{
  "model": "Qwen2.5-7B-Instruct",
  "quantization": "INT4",
  "router_accuracy": 0.93,
  "planner_accuracy": 0.88,
  "e2e_success_rate": 0.85,
  "avg_latency": 1.2,
  "cost_per_1k_tokens": 0.001
}
```

---

## 📅 Uygulama Timeline

### Hafta 1 (10-16 Şubat)
- [ ] Benchmark dataset hazırlama (200 router + 150 planner)
- [ ] Benchmark script yazma
- [ ] Baseline model (Qwen2.5-7B) ile ilk sonuçlar

### Hafta 2 (17-23 Şubat)
- [ ] Alternatif modelleri test etme (Llama, Mistral)
- [ ] Quantization deneyleri (FP16 vs INT4)
- [ ] Sonuç analizi ve raporlama

### Hafta 3 (24 Şubat - 2 Mart)
- [ ] En iyi modeli seçme
- [ ] Fine-tuning hazırlığı
- [ ] Production deployment planı

---

## 🎯 Başarı Kriterleri

| Metrik | Baseline | Hedef | Excellent |
|--------|----------|-------|-----------|
| Router Accuracy | 85% | 95% | 98% |
| Planner Accuracy | 75% | 90% | 95% |
| E2E Success Rate | 80% | 92% | 95% |
| Avg Latency (GPU) | 1.5s | 0.8s | 0.5s |
| Hallucination Rate | 5% | 1% | 0% |

---

## 🛠️ Test Edilecek Modeller

### Tier 1: Open-Source (Self-Hosted)
1. **Qwen2.5** (3B, 7B, 14B)
   - Pro: Türkçe desteği iyi, instruction-following güçlü
   - Con: Daha yeni, topluluk desteği az

2. **Llama 3.1** (8B, 70B)
   - Pro: En popüler, iyi benchmark sonuçları
   - Con: Türkçe orta seviye

3. **Mistral** (7B, Mixtral 8x7B)
   - Pro: Hızlı, tool-calling için optimize
   - Con: Quantized versiyonlarda performans düşüşü

4. **Gemma 2** (9B, 27B)
   - Pro: Google destekli, sürekli güncellemeler
   - Con: Tool-calling için native destek yok

### Tier 2: Commercial APIs (Karşılaştırma için)
1. **GPT-4 Turbo** (Baseline üst sınır)
2. **Claude 3.5 Sonnet**
3. **Gemini 1.5 Pro**

---

## 📈 Raporlama

### Günlük Metrikler
- Model başına benchmark sonuçları (CSV)
- Latency grafikleri
- Hata analizi

### Haftalık Rapor
- Model karşılaştırma tablosu
- En iyi performans gösteren modeller
- Öneriler ve sonraki adımlar

### Final Rapor
- Detaylı analiz (LaTeX PDF)
- Model seçim gerekçesi
- Production deployment planı

---

## 🚀 Tooling

### Gerekli Kütüphaneler
```bash
pip install transformers accelerate bitsandbytes
pip install scikit-learn matplotlib seaborn
pip install pandas numpy
pip install pytest tqdm
```

### Benchmark Notebooks
1. `benchmark_router.ipynb` - Router değerlendirme
2. `benchmark_planner.ipynb` - Planner değerlendirme
3. `benchmark_e2e.ipynb` - End-to-end test
4. `benchmark_comparison.ipynb` - Model karşılaştırma

---

**Son Güncelleme**: 10 Şubat 2026
