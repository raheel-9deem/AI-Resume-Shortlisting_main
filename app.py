import os
import pdfplumber
import docx
from flask import Flask , request

fl = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
fl.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

#Extract Text From Docx or PDF

def text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def text_from_docs(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

@fl.route('/')
def home():
    return "Resume Shortlister is running!"

@fl.route('/upload', methods = ['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        file = request.files['resume']
        file_path = os.path.join(fl.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

# Check File Extension
        if file.filename.endswith('.pdf'):
            extracted_text = text_from_pdf(file_path)
        elif file.filename.endswith('.docx'):
            extracted_text = text_from_docs(file_path)
        else:
            return 'Only PDF or DOCX files are allowed.'
        return f"File uploaded successfully: {file.filename}\n\nExtracted Text: {extracted_text}"
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume">
        <input type="submit" value="Upload Resume">
    </form>
    '''

if __name__ == '__main__':
    fl.run(debug=True)