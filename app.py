import base64
import os
import tempfile
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pdf2image import convert_from_path
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_LIST_URL = "http://localhost:11434/api/tags"
DEFAULT_MODEL = "glm-ocr:bf16"


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pdf-ocr-studio-secret-key-2026")


def pdf_to_images(pdf_path: Path, dpi: int = 100) -> list[Path]:
    """
    Convert a PDF file to a list of PNG image paths (one per page).
    Düşük DPI = daha hızlı işlem, daha küçük dosyalar
    """
    print(f"[DEBUG] PDF'i resimlere çeviriliyor: {pdf_path} (DPI: {dpi})")
    output_dir = pdf_path.parent / "pages"
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(str(pdf_path), dpi=dpi)
    print(f"[DEBUG] {len(pages)} sayfa bulundu")
    image_paths: list[Path] = []
    for i, page in enumerate(pages, start=1):
        # Resmi kaydet ve boyutunu logla
        img_path = output_dir / f"page_{i:03d}.png"
        
        # Eğer resim çok büyükse küçült (max 1600px genişlik)
        max_width = 1600
        if page.width > max_width:
            ratio = max_width / page.width
            new_height = int(page.height * ratio)
            page = page.resize((max_width, new_height))
            print(f"[DEBUG] Sayfa {i} yeniden boyutlandırıldı: {max_width}x{new_height}px")
        
        page.save(img_path, "PNG", optimize=True)
        file_size = img_path.stat().st_size / (1024 * 1024)  # MB
        print(f"[DEBUG] Sayfa {i} kaydedildi: {file_size:.2f} MB")
        image_paths.append(img_path)
    return image_paths


def image_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ocr_image_with_deepseek(image_path: Path, prompt: str, model_name: str) -> str:
    """
    Send a single image to OCR model via Ollama HTTP API.
    """
    print(f"[DEBUG] OCR başlıyor: {image_path.name} - Model: {model_name}")
    
    # Dosya boyutunu kontrol et
    file_size = image_path.stat().st_size / (1024 * 1024)  # MB
    print(f"[DEBUG] Resim boyutu: {file_size:.2f} MB")
    
    img_b64 = image_to_base64(image_path)
    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
    }
    print(f"[DEBUG] Ollama'ya istek gönderiliyor... (max 180 saniye)")
    
    # Timeout'u 3 dakikaya düşür, çok uzun sürerse zaten bir sorun var
    resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("response", "")
    print(f"[DEBUG] OCR tamamlandı, {len(result)} karakter döndü")
    return result


def ocr_pdf(pdf_path: Path, model_name: str, max_pages: int | None = None) -> str:
    """
    Run OCR on a PDF, page by page, and return concatenated markdown text.

    model_name: The Ollama model to use (e.g., 'deepseek-ocr:3b', 'glm-ocr:bf16')
    max_pages: If set, only process the first N pages (for very long PDFs).
    """
    print(f"[DEBUG] OCR_PDF başladı: {pdf_path.name} - Model: {model_name}")
    images = pdf_to_images(pdf_path)
    if max_pages is not None:
        images = images[:max_pages]
        print(f"[DEBUG] İlk {max_pages} sayfa işlenecek")

    all_text: list[str] = []
    for idx, img in enumerate(images, start=1):
        print(f"[DEBUG] Sayfa {idx}/{len(images)} işleniyor...")
        
        # Basit ve evrensel prompt (tüm modellerle uyumlu)
        prompt = "Extract all text from this image. Include everything you see."
        
        try:
            page_text = ocr_image_with_deepseek(img, prompt=prompt, model_name=model_name)
        except Exception as e:
            print(f"[ERROR] Sayfa {idx} hatası: {e}")
            page_text = f"Error on page {idx}: {e}"
        all_text.append(f"# Sayfa {idx}\n\n{page_text}\n")

    print(f"[DEBUG] OCR_PDF tamamlandı!")
    return "\n\n".join(all_text)


def get_available_models():
    """Ollama'dan mevcut modelleri listele"""
    try:
        resp = requests.get(OLLAMA_LIST_URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return models
    except Exception as e:
        print(f"[ERROR] Ollama modellerini listelerken hata: {e}")
        return []


@app.route("/", methods=["GET"])
def index():
    available_models = get_available_models()
    return render_template(
        "index.html",
        ocr_text=None,
        filename=None,
        available_models=available_models,
        selected_model=DEFAULT_MODEL,
    )


@app.route("/ocr", methods=["POST"])
def upload_and_ocr():
    print("[DEBUG] OCR isteği alındı")
    
    # Model seçimini al
    selected_model = request.form.get("model", DEFAULT_MODEL)
    print(f"[DEBUG] Seçilen model: {selected_model}")
    
    if "pdf_file" not in request.files:
        flash("PDF dosyası seçilmedi")
        return redirect(url_for("index"))

    file = request.files["pdf_file"]
    if file.filename == "":
        flash("PDF dosyası seçilmedi")
        return redirect(url_for("index"))

    if not file.filename.lower().endswith(".pdf"):
        flash("Sadece PDF dosyaları yüklenebilir")
        return redirect(url_for("index"))

    print(f"[DEBUG] PDF yüklendi: {file.filename}")
    # Geçici bir klasörde PDF'i sakla
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / file.filename
        file.save(pdf_path)
        print(f"[DEBUG] PDF kaydedildi: {pdf_path}")

        try:
            ocr_result = ocr_pdf(pdf_path, model_name=selected_model)
            print(f"[DEBUG] OCR başarılı, toplam {len(ocr_result)} karakter")
        except Exception as e:
            print(f"[ERROR] OCR hatası: {e}")
            flash(f"Hata: {e}")
            return redirect(url_for("index"))

    available_models = get_available_models()
    return render_template(
        "index.html",
        ocr_text=ocr_result,
        filename=file.filename,
        available_models=available_models,
        selected_model=selected_model,
    )


if __name__ == "__main__":
    # Lokalde geliştirme için
    app.run(host="0.0.0.0", port=8000, debug=True)

