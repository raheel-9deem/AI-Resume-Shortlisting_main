import os
import pdfplumber
import docx
import re
import spacy
from flask import Flask , request
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

fl = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
fl.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

nlp = spacy.load("en_core_web_sm")

# SKill Extractor From Large DB

skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

# Extract Text From PDF

def text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Extract Text From DOCX

def text_from_docs(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

#Skills Extractor
def skills_extract(text):
    try:
        annotations = skill_extractor.annotate(text)
        found = set()

        # Full SKill Match
        for match in annotations["results"]["full match"]:
            found.add(match["doc_node_value"])
        
        #Partial Match
        for match in annotations["results"]["ngram_scored"]:
            found.add(match["doc_node_value"])

        return list(found)
    except Exception as e:
        print("Skills Extraction Error", e)
        return []

# Email, Phone, Name Extraction

def extract_details(text):

    # Email Extraction
    email = re.findall(r'[a-zA-z0-9._/%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email[0] if email else "Not Found"

    # Phone Number Extraction
    match = re.search(r'(\+?\d{1,3}[-.\s]?)?\d{10,11}', text)
    phone = match.group(0) if match else "Not found"

    #Skills Extraction
    found_skills = skills_extract(text)

    # Names Extraction
    doc = nlp(text)
    name = "Not Found"
    for ent in doc.ents:
        if ent.label == "PERSON":
            name = ent.text
            break
    
    return {
        "name": name,
        "phone": phone,
        "email": email,
        "skills": found_skills
    }
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

        details = extract_details(extracted_text)

        return f"""
        <h3>Uploaded: {file.filename}</h3>
        <p><b>Name:</b> {details['name']}</p>
        <p><b>Email:</b> {details['email']}</p>
        <p><b>Phone:</b> {details['phone']}</p>
        <p><b>Skills:</b> {', '.join(details['skills']) if details['skills'] else 'None found'}</p>
        """
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume">
        <input type="submit" value="Upload Resume">
    </form>
    '''

if __name__ == '__main__':
    fl.run(debug=True)