# 📝 AI Resume Analyzer

A web app that reviews your resume PDF, compares it with a job description, and gives an ATS-style keyword match score plus AI feedback and suggestions.

## Demo
<img width="1920" height="1080" alt="Screenshot 2026-11-19 131548" src="https://github.com/user-attachments/assets/9f1c5230-6d94-4eb3-9277-e57045e4ccfc" />



## Features
- Upload a resume PDF and paste any job description
- **Instant local check (no AI):** word count, skills detected, section check, contact details, keyword match % against the job
- **AI review (Gemini):** overall score, strengths, weaknesses, missing skills, specific suggestions, and a rewritten profile summary
- Automatic fallback to backup Gemini models when one is busy
- Resume text is never stored by the app

## How it works
```
PDF -> extract text (pypdf)
    -> local analysis: skill matching + section/contact checks + match %
    -> Gemini API: structured JSON review -> displayed in Streamlit
```

## Tech stack
Python, Streamlit, pypdf, Google Gemini API, python-dotenv

## Run it locally
```bash
git clone https://github.com/<your-username>/ai-resume-analyzer.git
cd ai-resume-analyzer

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

copy .env.example .env         # Windows (Mac/Linux: cp .env.example .env)
# open .env and paste your free key from https://aistudio.google.com/apikey

streamlit run app.py
```

## Project structure
```
ai-resume-analyzer/
├── app.py            # Streamlit UI
├── analyzer.py       # local analysis (skills, sections, match %)
├── ai.py             # Gemini API call + JSON parsing + model fallback
├── requirements.txt
├── .env.example      # template for the API key
└── README.md
```

## Limitations
- Scanned (image-only) PDFs are not supported
- Skill matching uses a built-in keyword list; unusual skills may be missed
- AI scores are guidance, not an exact ATS result

## Future improvements
- Export the report as PDF
- Support DOCX resumes
- Bigger skills database and synonym matching
