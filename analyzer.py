"""
analyzer.py - the LOCAL part of the resume analysis (no AI, no internet needed).

It reads the PDF, finds skills, checks sections and contact info, and compares
the resume with a job description to compute a keyword match percentage.
"""

import io
import re

from pypdf import PdfReader

# Skills we look for (add your own!)
SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "html", "css",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
    "spring boot", "mongodb", "mysql", "postgresql", "sqlite", "redis", "firebase",
    "git", "github", "docker", "kubernetes", "aws", "azure", "gcp", "linux",
    "rest api", "graphql", "microservices", "ci/cd", "jenkins",
    "machine learning", "deep learning", "nlp", "computer vision", "opencv",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
    "data analysis", "data structures", "algorithms", "oop", "streamlit",
    "rag", "langchain", "llm", "prompt engineering", "power bi", "tableau", "excel",
    "agile", "scrum", "jira", "testing", "unit testing", "selenium", "figma",
    "cybersecurity", "networking", "kotlin", "swift", "flutter", "android",
    "communication", "teamwork", "problem solving", "leadership",
]

SECTIONS = {
    "Summary / Profile": ["summary", "profile", "objective", "about me"],
    "Education": ["education", "academic"],
    "Skills": ["skills", "technical skills"],
    "Projects": ["projects", "project"],
    "Experience / Internship": ["experience", "internship", "work history", "employment"],
    "Certifications": ["certification", "certifications", "courses"],
}


def extract_text(file_bytes):
    """Read all text from a PDF given as bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages).strip()


def find_skills(text):
    """Return the list of known skills mentioned in the text."""
    low = text.lower()
    found = []
    for skill in SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, low):
            found.append(skill)
    return found


def contact_info(text):
    """Check which contact details are present."""
    low = text.lower()
    return {
        "Email": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)),
        "Phone": bool(re.search(r"(\+?\d[\d\s\-]{8,}\d)", text)),
        "LinkedIn": "linkedin.com" in low,
        "GitHub": "github.com" in low,
    }


def sections_present(text):
    """Check which standard resume sections exist."""
    low = text.lower()
    return {
        name: any(word in low for word in words) for name, words in SECTIONS.items()
    }


def local_report(resume_text, jd_text=""):
    """Compute everything that doesn't need AI."""
    resume_skills = find_skills(resume_text)
    jd_skills = find_skills(jd_text) if jd_text.strip() else []

    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]
    match_pct = round(100 * len(matched) / len(jd_skills)) if jd_skills else None

    return {
        "word_count": len(resume_text.split()),
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing,
        "match_pct": match_pct,
        "contact": contact_info(resume_text),
        "sections": sections_present(resume_text),
    }
