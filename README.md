# AI-Based Resume Shortlisting

A Flask-powered web application that parses uploaded resumes (PDF or DOCX), extracts key candidate details, and displays them in the browser. It combines rule-based extraction (regex, spaCy) with a large-skill knowledge base and an LLM call for name extraction.

## Features

- **Resume upload** — simple HTML form (`/upload`) accepting `.pdf` and `.docx` files.
- **Text extraction** — uses `pdfplumber` for PDFs and `python-docx` for Word documents.
- **Contact extraction** — email and phone number via regular expressions.
- **Name extraction** — sends the first 400 characters of the resume to Claude and asks for the candidate's full name only.
- **Skills extraction** — uses [SkillNer](https://github.com/aryashiv20/SkillNer) against its full skill knowledge base (`SKILL_DB`), returning both full matches and scored n-gram partial matches.
- **Result page** — renders the extracted name, email, phone, and skills as HTML.

## Project Structure

```
Resume-shortlisted/
├── app.py              # Single-file Flask application (all logic lives here)
├── uploads/            # Directory where uploaded resumes are temporarily saved
└── README.md           # This file
```

## How It Works

1. A user visits `/upload` and submits a resume file.
2. The file is saved to the `uploads/` folder.
3. Based on the file extension, text is extracted via `text_from_pdf()` or `text_from_docs()`.
4. `extract_details()` runs four extractors over the text:
   - **Email** — first matching email address.
   - **Phone** — first 10–11 digit number, with optional international prefix.
   - **Skills** — `SkillExtractor.annotate()` against `SKILL_DB`.
   - **Name** — Claude LLM call on the top of the resume.
5. The extracted details are returned as an HTML response.

## API Endpoints

| Method | Route     | Description                                      |
|--------|-----------|--------------------------------------------------|
| GET    | `/`       | Health-check — confirms the app is running.      |
| GET/POST | `/upload` | GET shows the upload form; POST processes a resume. |

## Installation

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS / Linux

# Install Python dependencies
pip install flask pdfplumber python-docx spacy anthropic skillNer

# Download the small English spaCy model
python -m spacy download en_core_web_sm
```

## Configuration

Before running the app, edit `app.py` and replace the placeholder credentials in the Anthropic client:

```python
claude_client = anthropic.Anthropic(
    base_url = "Paste Your Claude API Base URL Here",
    api_key = "Paste Your Claude API Here"
)
```

Set your actual Claude API base URL and API key. The model is set to `"auto"`.

## Running the App

```bash
python app.py
```

The Flask development server starts on `http://127.0.0.1:5000` with `debug=True`. Navigate to `/upload` to upload a resume.

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
- Uploaded files are saved to disk in `uploads/`; there is no cleanup/expiration logic.
- The app runs with Flask's debug server and is intended for local/development use, not production deployment.
- Any exception during skill or name extraction is caught and logged, returning an empty skill list or `"Not found"` for the name.
