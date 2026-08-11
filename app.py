
from flask import Flask, render_template, request, send_file
from pdf2docx import Converter
# from docx2pdf import convert
from PIL import Image
from werkzeug.utils import secure_filename
import os
import threading
import time

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SIZE_LIMITS = {
    "jpg": 10 * 1024 * 1024,
    "jpeg": 10 * 1024 * 1024,
    "png": 10 * 1024 * 1024,
    "pdf": 20 * 1024 * 1024,
    "doc": 20 * 1024 * 1024,
    "docx": 20 * 1024 * 1024,
}

def auto_delete(path, delay=120):
    time.sleep(delay)
    for _ in range(5):
        try:
            if os.path.exists(path):
                os.remove(path)
                print("Deleted:", path)
            return
        except PermissionError:
            time.sleep(5)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert_file():
    if "file" not in request.files:
        return "No file selected.", 400

    file = request.files["file"]
    conversion_type = request.form.get("conversion","")

    if file.filename == "":
        return "No file selected.", 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".",1)[-1].lower()

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if ext in SIZE_LIMITS and size > SIZE_LIMITS[ext]:
        return f"Maximum allowed size for .{ext} is {SIZE_LIMITS[ext]//1024//1024} MB.",400

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    base = os.path.splitext(filename)[0]

    try:
        if conversion_type == "pdf_to_word":
            output_path = os.path.join(OUTPUT_FOLDER, base + ".docx")
            cv = Converter(filepath)
            cv.convert(output_path)
            cv.close()

        # W-t-P needed Libreoffice.

        # elif conversion_type == "word_to_pdf":
        #     output_path = os.path.join(OUTPUT_FOLDER, base + ".pdf")
        #     convert(filepath, output_path)


        elif conversion_type == "jpg_to_png":
            output_path = os.path.join(OUTPUT_FOLDER, base + ".png")
            Image.open(filepath).save(output_path, "PNG")
        elif conversion_type == "png_to_jpg":
            output_path = os.path.join(OUTPUT_FOLDER, base + ".jpg")
            Image.open(filepath).convert("RGB").save(output_path, "JPEG")
        elif conversion_type in ("jpg_to_pdf","png_to_pdf"):
            output_path = os.path.join(OUTPUT_FOLDER, base + ".pdf")
            Image.open(filepath).convert("RGB").save(output_path)
        else:
            return "Invalid conversion type.",400
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    threading.Thread(target=auto_delete,args=(output_path,120),daemon=True).start()
    return render_template("download.html", filename=os.path.basename(output_path))

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
    if not os.path.exists(path):
        return "File expired. Please convert again.",404
    return send_file(path, as_attachment=True)

@app.route("/privacy")
def privacy():
    return render_template("privacy-policy.html")

@app.route("/file-requirements")
def file_requirements():
    return render_template("file-requirements.html")

@app.errorhandler(413)
def too_large(e):
    return "File too large. Maximum upload size is 25 MB.",413

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
