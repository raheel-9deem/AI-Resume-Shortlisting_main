import os
import pdfplumber
import docx
import re
import traceback
import spacy
import anthropic
from flask import Flask, request
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

fl = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
fl.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

nlp = spacy.load("en_core_web_sm")

# Import Claude For Name Extracting

claude_client = anthropic.Anthropic(
    base_url="https://api.hcnsec.cn/sign-up?aff=1VKI",
    api_key = os.environ.get("ANTHROPIC_API_KEY")
)

current_jd = ""

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


def match_resume_to_jd(resume_skills, resume_text, jd_text):
    try:
        prompt = f"""
        You are a recruiter assistant. Compare this candidate's resume against the job description.

        Job Description:
        {jd_text}

        Candidate's extracted skills:
        {', '.join(resume_skills) if resume_skills else 'None extracted'}

        Candidate's resume text (for context):
        {resume_text[:1500]}

        Give a match score out of 100, and a short 2-3 line reasoning explaining why.
        Reply in EXACTLY this format:
        Score: <number>
        Reasoning: <your reasoning>
        """
        message = claude_client.messages.create(
            model="auto",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        text_only = ""
        if message.content:
            for block in message.content:
                if hasattr(block, "text"):
                    text_only += block.text
        return text_only.strip()
    except Exception:
        print("----- Match Resume To JD Error -----")
        traceback.print_exc()
        return "Score: 0\nReasoning: Matching failed due to an error."


# SKill Extractor From Large DB

skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

def skills_extract(text):
    try:
        annotations = skill_extractor.annotate(text)
        found = set()

        # Full Skill Match
        for match in annotations["results"]["full_matches"]:
            found.add(match["doc_node_value"])

        # Partial Match
        for match in annotations["results"]["ngram_scored"]:
            found.add(match["doc_node_value"])

        return list(found)
    except Exception:
        print("---- SKILL EXTRACTION ERROR (full details) ----")
        traceback.print_exc()
        print("------------------------------------------------")
        return []


# Name Extractor DEF

def name_extract(text):
    try:
        top_text = text[:400]

        message = claude_client.messages.create(
            model="auto",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"Extract only the candidate's full name from this resume text. Reply with ONLY the name, nothing else. If no name is found, reply with 'Not found'.\n\nResume text:\n{top_text}"
            }]
        )

        text_only = ""
        if message.content:
            for block in message.content:
                if hasattr(block, "text"):
                    text_only += block.text

        return text_only.strip() or "Not found"
    except Exception:
        print("----- Name Extraction Error -----")
        traceback.print_exc()
        return "Not found"


# Email, Phone, Name Extraction

def extract_details(text):

    # Email Extraction
    email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email[0] if email else "Not Found"

    # Phone Number Extraction
    match = re.search(r'(\+?\d{1,3}[-.\s]?)?\d{10,11}', text)
    phone = match.group(0) if match else "Not found"

    # Skills Extraction
    found_skills = skills_extract(text)

    # Names Extraction
    name = name_extract(text)

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "skills": found_skills
    }


@fl.route('/')
def home():
    return "======== AI Based Resume Shortlisting Project Is Running ========"


@fl.route('/jd', methods=['GET', 'POST'])
def set_jd():
    global current_jd

    if request.method == 'POST':
        current_jd = request.form['jd_text']
        return f"<p>Job description saved successfully</p><p style='color: #2a9d8f; font-weight: bold;'>{current_jd}</p><p><a href='/upload'>Go to upload resumes</a></p>"

    return '''
    <form method="POST">
        <textarea name="jd_text" rows="15" cols="70" placeholder="Paste job description here..."></textarea><br><br>
        <input type="submit" value="Save Job Description">
    </form>
    '''


@fl.route('/upload', methods=['GET', 'POST'])
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

        match_result_html = ""
        if current_jd.strip():
            match_result = match_resume_to_jd(details["skills"], extracted_text, current_jd)
            match_result_html = f"<hr><h4>Match Result</h4><pre>{match_result}</pre>"
        else:
            match_result_html = "<p><i>No job description set yet. Set one at /jd to see match score.</i></p>"

        return f"""
        <h3>Uploaded: {file.filename}</h3>
        <p><b>Name:</b> {details['name']}</p>
        <p><b>Email:</b> {details['email']}</p>
        <p><b>Phone:</b> {details['phone']}</p>
        <p><b>Skills:</b> {', '.join(details['skills']) if details['skills'] else 'None found'}</p>
        {match_result_html}
        """
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume">
        <input type="submit" value="Upload Resume">
    </form>
    '''


if __name__ == '__main__':
    fl.run(debug=True)