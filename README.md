# AI-Based Resume Shortlisting

A Flask-powered web application that parses uploaded resumes (PDF or DOCX), extracts key candidate details, and displays them in the browser. It also supports setting a Job Description and getting a match score comparing the candidate's resume against it. It combines rule-based extraction (regex, spaCy) with a large-skill knowledge base and LLM calls for name extraction and match scoring.

## Features

- **Resume upload** — simple HTML form (`/upload`) accepting `.pdf` and `.docx` files.
- **Text extraction** — uses `pdfplumber` for PDFs and `python-docx` for Word documents.
- **Contact extraction** — email and phone number via regular expressions.
- **Name extraction** — sends the first 400 characters of the resume to Claude and asks for the candidate's full name only.
- **Skills extraction** — uses [SkillNer](https://github.com/aryashiv20/SkillNer) against its full skill knowledge base (`SKILL_DB`), returning both full matches and scored n-gram partial matches.
- **Resume-to-JD Match** — compares the candidate's skills and resume text against a saved Job Description using Claude, returning a match score (out of 100) and reasoning.
- **Job Description route** — a dedicated `/jd` route to input and save a Job Description that persists in memory for matching.

## Project Structure

```
Resume-shortlisted/
├── app.py        # Single-file Flask application (all logic lives here)
├── uploads/      # Directory where uploaded resumes are temporarily saved
├── requirements.txt  # Python dependencies
└── README.md     # This file
```

## How It Works

1. A user visits `/jd` and submits a Job Description (saved in-memory).
2. The user then visits `/upload` and submits a resume file.
3. The file is saved to the `uploads/` folder.
4. Based on the file extension, text is extracted via `text_from_pdf()` or `text_from_docs()`.
5. `extract_details()` runs four extractors over the text:
   - **Email** — first matching email address.
   - **Phone** — first 10–11 digit number, with optional international prefix.
   - **Skills** — `SkillExtractor.annotate()` against `SKILL_DB`.
   - **Name** — Claude LLM call on the top of the resume.
6. If a Job Description has been set, `match_resume_to_jd()` sends the candidate's skills and resume text to Claude along with the JD and returns a score out of 100 with reasoning.
7. The extracted details and match result (if any) are returned as an HTML response.

## API Endpoints

| Method | Route   | Description |
|--------|---------|-------------|
| GET    | `/`     | Health-check — confirms the app is running. |
| GET/POST | `/jd` | GET shows the JD form; POST saves the job description in memory. |
| GET/POST | `/upload` | GET shows the upload form; POST processes a resume and displays extracted details with match score. |

## Installation

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS / Linux

# Install all dependencies
pip install -r requirements.txt

# Download the small English spaCy model
python -m spacy download en_core_web_sm
```

## Configuration

Before running the app, set the `ANTHROPIC_API_KEY` environment variable. The Claude client base URL is set in the code:

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "your-api-key"

# Windows (cmd)
set ANTHROPIC_API_KEY=your-api-key

# macOS / Linux
export ANTHROPIC_API_KEY=your-api-key
```

## Running the App

```bash
python app.py
```

The Flask development server starts on `http://127.0.0.1:5000` with `debug=True`.

## Usage

1. Navigate to `http://127.0.0.1:5000/jd` and paste a Job Description, then click **Save Job Description**.
2. Navigate to `http://127.0.0.1:5000/upload` and upload a resume file (PDF or DOCX).
3. The page will display the candidate's **Name**, **Email**, **Phone**, **Skills**, and a **Match Result** (score out of 100 + reasoning) against the saved job description.

## Dependencies

- [Flask](https://flask.palletsprojects.com/) — web framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF text extraction
- [python-docx](https://github.com/python-openxml/python-docx) — DOCX text extraction
- [spaCy](https://spacy.io/) (`en_core_web_sm`) — NLP pipeline for SkillNer
- [SkillNer](https://github.com/aryashiv20/SkillNer) — skill/knowledge extraction from text
- [anthropic](https://github.com/anthropics/anthropic-sdk-python) — Claude LLM client

## Notes & Limitations

- Only the **first** email and phone match are returned; additional matches are discarded.
- The phone regex matches a single 10–11 digit number with an optional country code prefix.
- Name extraction relies on an LLM call and is limited to the first 400 characters of the resume — it returns `"Not found"` on failure.
- The Job Description is stored **in-memory** — it resets when the server restarts.
- Uploaded files are saved to disk in `uploads/`; there is no cleanup/expiration logic.
- The app runs with Flask's debug server and is intended for local/development use, not production deployment.
- Any exception during skill or name extraction is caught and logged, returning an empty skill list or `"Not found"` for the name.
- If no Job Description is set, the match score section will prompt the user to set one at `/jd`.
