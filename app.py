import os
import zipfile
from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route (where the user can upload PDFs)
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    
    files = request.files.getlist('file')
    zip_filename = 'inverted_colors_pdfs.zip'
    zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)

    # Create a new ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Loop through each uploaded PDF
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                # Invert the colors of the PDF and save the new PDF
                inverted_pdf_path = invert_pdf_colors(filepath)
                zipf.write(inverted_pdf_path, os.path.basename(inverted_pdf_path))
                os.remove(inverted_pdf_path)  # Clean up the inverted PDF after adding it to the ZIP

    return send_file(zip_path, as_attachment=True)

# Function to invert colors of PDF pages
def invert_pdf_colors(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF
    inverted_pdf_path = os.path.join(OUTPUT_FOLDER, f'inverted_colors_{os.path.basename(pdf_path)}')
    inverted_doc = fitz.open()  # Create an empty PDF

    # Loop through each page and invert its colors
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # Get the page
        pix = page.get_pixmap()  # Render page to an image

        # Convert the image (pixmap) to PIL Image for easy color inversion
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        inverted_img = ImageOps.invert(img.convert("RGB"))  # Invert colors

        # Save the inverted image as a temporary PNG file
        temp_image_path = os.path.join(OUTPUT_FOLDER, f'temp_inverted_{page_num}.png')
        inverted_img.save(temp_image_path)

        # Add the inverted image as a new page in the PDF
        inverted_doc.new_page(width=page.rect.width, height=page.rect.height)
        inverted_doc[-1].insert_image(inverted_doc[-1].rect, filename=temp_image_path)

        os.remove(temp_image_path)  # Clean up temporary image file

    inverted_doc.save(inverted_pdf_path)  # Save the new PDF
    return inverted_pdf_path

if __name__ == '__main__':
    app.run(debug=True)
