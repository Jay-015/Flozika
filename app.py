from flask import Flask, render_template, request, send_file
from pdf2docx import Converter
from PIL import Image
from pypdf import PdfReader
from werkzeug.utils import secure_filename

import os
import threading
import time


# =========================================================
# Flask App Configuration
# =========================================================

app = Flask(__name__)

# Maximum request size: 25 MB
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


# =========================================================
# Folder Configuration
# =========================================================

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# File Size Limits
# =========================================================

SIZE_LIMITS = {
    "jpg": 10 * 1024 * 1024,      # 10 MB
    "jpeg": 10 * 1024 * 1024,     # 10 MB
    "png": 10 * 1024 * 1024,      # 10 MB
    "pdf": 10 * 1024 * 1024,      # 10 MB
    "doc": 20 * 1024 * 1024,      # 20 MB
    "docx": 20 * 1024 * 1024,     # 20 MB
}


# =========================================================
# Automatic File Delete Function
# =========================================================

def auto_delete(path, delay=120):
    """
    Delete the output file automatically after the given delay.

    Default delay:
    120 seconds = 2 minutes
    """

    time.sleep(delay)

    for _ in range(5):
        try:
            if os.path.exists(path):
                os.remove(path)
                print("Deleted:", path)

            return

        except PermissionError:
            time.sleep(5)


# =========================================================
# Home Page
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# File Conversion Route
# =========================================================

@app.route("/convert", methods=["POST"])
def convert_file():

    # -----------------------------------------------------
    # Check if file exists
    # -----------------------------------------------------

    if "file" not in request.files:
        return "No file selected.", 400

    file = request.files["file"]
    conversion_type = request.form.get("conversion", "")

    if file.filename == "":
        return "No file selected.", 400


    # -----------------------------------------------------
    # Secure filename and extension
    # -----------------------------------------------------

    filename = secure_filename(file.filename)

    if "." not in filename:
        return "Invalid file type.", 400

    ext = filename.rsplit(".", 1)[-1].lower()


    # -----------------------------------------------------
    # Check file size
    # -----------------------------------------------------

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if ext in SIZE_LIMITS and size > SIZE_LIMITS[ext]:

        max_size_mb = SIZE_LIMITS[ext] // 1024 // 1024

        return (
            f"Maximum allowed size for .{ext} "
            f"is {max_size_mb} MB.",
            400
        )


    # -----------------------------------------------------
    # Save uploaded file temporarily
    # -----------------------------------------------------

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)


    # -----------------------------------------------------
    # PDF Page Limit
    # -----------------------------------------------------

    if ext == "pdf":

        try:
            reader = PdfReader(filepath, strict=False)
            page_count = len(reader.pages)

            # Maximum 15 pages
            if page_count > 15:

                if os.path.exists(filepath):
                    os.remove(filepath)

                return (
                    "PDF can contain a maximum of 15 pages.",
                    400
                )

        except Exception:

            if os.path.exists(filepath):
                os.remove(filepath)

            return (
                "Invalid or unsupported PDF file.",
                400
            )


    # -----------------------------------------------------
    # File base name
    # -----------------------------------------------------

    base = os.path.splitext(filename)[0]

    output_path = None


    # =====================================================
    # Conversion Process
    # =====================================================

    try:

        # -------------------------------------------------
        # PDF → Word
        # -------------------------------------------------

        if conversion_type == "pdf_to_word":

            output_path = os.path.join(
                OUTPUT_FOLDER,
                base + ".docx"
            )

            cv = None

            try:

                cv = Converter(filepath)

                cv.convert(output_path)

            finally:

                if cv is not None:
                    cv.close()


        # -------------------------------------------------
        # Word → PDF
        # -------------------------------------------------

        # LibreOffice is required for Word → PDF.
        #
        # Example:
        #
        # elif conversion_type == "word_to_pdf":
        #     output_path = os.path.join(
        #         OUTPUT_FOLDER,
        #         base + ".pdf"
        #     )
        #
        #     convert(filepath, output_path)


        # -------------------------------------------------
        # JPG → PNG
        # -------------------------------------------------

        elif conversion_type == "jpg_to_png":

            output_path = os.path.join(
                OUTPUT_FOLDER,
                base + ".png"
            )

            with Image.open(filepath) as img:
                img.save(output_path, "PNG")


        # -------------------------------------------------
        # PNG → JPG
        # -------------------------------------------------

        elif conversion_type == "png_to_jpg":

            output_path = os.path.join(
                OUTPUT_FOLDER,
                base + ".jpg"
            )

            with Image.open(filepath) as img:

                img.convert("RGB").save(
                    output_path,
                    "JPEG"
                )


        # -------------------------------------------------
        # JPG / PNG → PDF
        # -------------------------------------------------

        elif conversion_type in ("jpg_to_pdf", "png_to_pdf"):

            output_path = os.path.join(
                OUTPUT_FOLDER,
                base + ".pdf"
            )

            with Image.open(filepath) as img:

                img.convert("RGB").save(
                    output_path
                )


        # -------------------------------------------------
        # Invalid Conversion
        # -------------------------------------------------

        else:

            return "Invalid conversion type.", 400


    # =====================================================
    # Conversion Error Handling
    # =====================================================

    except Exception as e:

        print("Conversion Error:", str(e))

        # Delete incomplete output file
        if output_path and os.path.exists(output_path):

            try:
                os.remove(output_path)

            except Exception:
                pass

        return (
            "Conversion failed. Please try again with a "
            "smaller or supported file.",
            500
        )


    # =====================================================
    # Delete Input File
    # =====================================================

    finally:

        if os.path.exists(filepath):

            try:
                os.remove(filepath)

            except Exception:
                pass


    # =====================================================
    # Check Output File
    # =====================================================

    if not output_path or not os.path.exists(output_path):

        return (
            "Conversion failed. Output file was not created.",
            500
        )


    # =====================================================
    # Automatic Output File Delete
    # =====================================================

    threading.Thread(
        target=auto_delete,
        args=(output_path, 120),
        daemon=True
    ).start()


    # =====================================================
    # Download Page
    # =====================================================

    return render_template(
        "download.html",
        filename=os.path.basename(output_path)
    )


# =========================================================
# Download Route
# =========================================================

@app.route("/download/<filename>")
def download(filename):

    path = os.path.join(
        OUTPUT_FOLDER,
        secure_filename(filename)
    )

    if not os.path.exists(path):

        return (
            "File expired. Please convert again.",
            404
        )

    return send_file(
        path,
        as_attachment=True
    )


# =========================================================
# Privacy Policy
# =========================================================

@app.route("/privacy")
def privacy():

    return render_template(
        "privacy-policy.html"
    )


# =========================================================
# File Requirements
# =========================================================

@app.route("/file-requirements")
def file_requirements():

    return render_template(
        "file-requirements.html"
    )


# =========================================================
# File Too Large Error
# =========================================================

@app.errorhandler(413)
def too_large(e):

    return (
        "File too large. Maximum upload size is 25 MB.",
        413
    )


# =========================================================
# Run Flask App
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=8000
    )