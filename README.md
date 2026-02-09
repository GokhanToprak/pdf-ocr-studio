# PDF OCR Studio

PDF dosyalarını lokal OCR modelleri ile metne dönüştüren modern web uygulaması.

## ✨ Özellikler

- 🎯 **Model Seçimi**: Ön yüzde istediğin Ollama modelini seç
- 🚀 **Lokal İşlem**: Tüm OCR işlemleri bilgisayarında gerçekleşir
- 📄 **PDF Desteği**: Çok sayfalı PDF'leri otomatik işle
- 📝 **Markdown Çıktı**: Her sayfa markdown formatında
- ✏️ **Düzenlenebilir**: Çıktıyı anında düzenle, kopyala veya indir
- 🎨 **Modern Arayüz**: Şık, karanlık tema ile kullanıcı dostu tasarım

## 📋 Gereksinimler

### 1. Ollama Kurulumu

```bash
# MacOS
curl -fsSL https://ollama.com/install.sh | sh

# Ollama'yı başlat (bazı kurulumlarda otomatik başlar)
ollama serve
```

### 2. OCR Modellerini İndir

En az bir OCR modeli indir:

```bash
# Önerilen modeller:
ollama pull deepseek-ocr:3b    # DeepSeek OCR 3B (~6.7 GB)
ollama pull glm-ocr:bf16        # GLM OCR BF16 (~2.2 GB, daha hızlı)

# Sisteminde yüklü modelleri listele:
ollama list
```

### 3. Poppler (PDF işleme için)

```bash
# MacOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Poppler binary'lerini indir: https://blog.alivate.com.au/poppler-windows/
```

### 4. Python Bağımlılıkları

```bash
pip install -r requirements.txt
```

## 🚀 Kullanım

### 1. Uygulamayı Başlat

```bash
cd deepseek-ocr
python3 app.py
```

Uygulama `http://localhost:8000` adresinde çalışacak.

### 2. Tarayıcıdan Kullan

1. `http://localhost:8000` adresine git
2. **OCR Modeli Seç** dropdown'ından istediğin modeli seç
3. **PDF Seç** butonundan PDF dosyanı yükle
4. **OCR Başlat** butonuna bas
5. Sağ taraftaki alanda OCR çıktısını gör, düzenle, kopyala veya `.md` olarak indir

## 🎛️ Model Karşılaştırması

| Model | Boyut | Hız | Doğruluk | Önerilen Kullanım |
|-------|-------|-----|----------|-------------------|
| `deepseek-ocr:3b` | 6.7 GB | Yavaş | Yüksek | Karmaşık layoutlar, tablolar |
| `glm-ocr:bf16` | 2.2 GB | Hızlı | Orta-Yüksek | Genel kullanım, hızlı işlem |
| `llava:7b` | 4.7 GB | Orta | Orta | Görsel içerik ağırlıklı |
| `qwen2.5vl:7b` | 6.0 GB | Orta | Yüksek | Çok dilli, karmaşık yapılar |

## ⚙️ Yapılandırma

### DPI Ayarlama (Görüntü Kalitesi)

`app.py` dosyasında:

```python
def pdf_to_images(pdf_path: Path, dpi: int = 150) -> list[Path]:
    # dpi değerini artır (örn: 200, 300) -> daha yüksek kalite, daha yavaş
    # dpi değerini azalt (örn: 100, 120) -> daha düşük kalite, daha hızlı
```

### Timeout Ayarlama

Çok uzun süren işlemler için `app.py` içinde:

```python
resp = requests.post(OLLAMA_URL, json=payload, timeout=600)  # 10 dakika
```

## 🐛 Sorun Giderme

### "Ollama'ya bağlanamıyor"

```bash
# Ollama'nın çalıştığını kontrol et:
curl http://localhost:11434/api/tags

# Çalışmıyorsa başlat:
ollama serve
```

### "Model bulunamadı"

```bash
# Yüklü modelleri listele:
ollama list

# İstediğin modeli indir:
ollama pull deepseek-ocr:3b
```

### "pdf2image hatası"

```bash
# Poppler kurulu değilse:
brew install poppler  # MacOS
```

### OCR çok yavaş

- DPI'yi düşür (150 → 100)
- Daha hızlı bir model seç (`glm-ocr:bf16`)
- GPU varsa Ollama GPU desteği aktif mi kontrol et

## 📁 Proje Yapısı

```
deepseek-ocr/
├── app.py                 # Flask backend
├── templates/
│   └── index.html         # Ön yüz arayüzü
├── requirements.txt       # Python bağımlılıkları
└── README.md             # Bu dosya
```

## 🔮 Gelecek Geliştirmeler

- [ ] Online API desteği (DeepSeek resmi API)
- [ ] Batch işleme (çoklu PDF yükleme)
- [ ] Sayfa sınırı ayarı (ilk N sayfa)
- [ ] Özel prompt desteği
- [ ] OCR sonuçlarını kaydetme/geçmiş

## 📄 Lisans

MIT License

## 🤝 Katkı

Pull request'ler memnuniyetle karşılanır!

---

**Not**: Bu uygulama tamamen lokal çalışır, hiçbir veri dışarıya gönderilmez.
