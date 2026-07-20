import os
import pdfplumber
import docx
from flask import Flask, request

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


@app.route("/")
def home():
    return "Resume Shortlister is running!"


@app.route("/upload", methods=["GET", "POST"])
def upload_resume():
    if request.method == "POST":
        file = request.files["resume"]
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        # File extension check karo
        if file.filename.endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_path)
        elif file.filename.endswith(".docx"):
            extracted_text = extract_text_from_docx(file_path)
        else:
            return "Only PDF or DOCX files allowed."

        return f"<h3>Uploaded: {file.filename}</h3><pre>{extracted_text}</pre>"

    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume">
        <input type="submit" value="Upload Resume">
    </form>
    '''


if __name__ == "__main__":
    app.run(debug=True)