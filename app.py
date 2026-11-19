"""
app.py - Streamlit web interface for the AI Resume Analyzer.
Run with:  streamlit run app.py
"""

import streamlit as st

import ai
import analyzer

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📝", layout="wide")
st.title("📝 AI Resume Analyzer")
st.caption("Upload your resume, paste a job description, and get an ATS-style match score and AI feedback.")

with st.sidebar:
    st.header("About")
    st.write(
        "1. Upload your resume (PDF)\n"
        "2. Paste a job description (optional)\n"
        "3. Click **Analyze**"
    )
    st.info(
        "🔒 Privacy: your resume text is sent to Google Gemini for the AI review. "
        "Nothing is stored by this app."
    )
    st.caption(
        f"Model: {ai.GEMINI_MODEL}  \n"
        f"API key loaded: {'Yes' if ai.key_loaded() else 'NO - check .env'}"
    )

left, right = st.columns(2)
with left:
    resume_file = st.file_uploader("Upload resume (PDF)", type="pdf")
with right:
    jd_text = st.text_area(
        "Job description (optional but recommended)",
        height=200,
        placeholder="Paste the job posting here to get a match score...",
    )

if st.button("🔍 Analyze", type="primary"):
    if not resume_file:
        st.warning("Please upload your resume PDF first.")
        st.stop()

    # ---------- read the PDF ----------
    try:
        resume_text = analyzer.extract_text(resume_file.getvalue())
    except Exception as error:
        st.error(f"Could not read this PDF ({error}). Try another file.")
        st.stop()

    if len(resume_text) < 50:
        st.error("No readable text found. Scanned/image PDFs are not supported.")
        st.stop()

    # ---------- local analysis (instant) ----------
    report = analyzer.local_report(resume_text, jd_text)

    st.header("1. Quick check (instant, no AI)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Word count", report["word_count"])
    c2.metric("Skills found", len(report["resume_skills"]))
    if report["match_pct"] is not None:
        c3.metric("Keyword match with job", f"{report['match_pct']}%")
    else:
        c3.metric("Keyword match with job", "n/a")

    if report["match_pct"] is not None:
        st.progress(report["match_pct"] / 100)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Sections")
        for name, present in report["sections"].items():
            st.write(("✅ " if present else "❌ ") + name)
    with col_b:
        st.subheader("Contact details")
        for name, present in report["contact"].items():
            st.write(("✅ " if present else "❌ ") + name)

    if report["resume_skills"]:
        st.write("**Skills detected:** " + ", ".join(report["resume_skills"]))
    if report["jd_skills"]:
        st.write("**✅ Matched with job:** " + (", ".join(report["matched"]) or "none"))
        st.write("**❌ Missing from resume:** " + (", ".join(report["missing"]) or "none 🎉"))

    # ---------- AI analysis ----------
    st.header("2. AI review")
    with st.spinner("Gemini is reading your resume..."):
        data, message = ai.analyze(resume_text, jd_text)

    if data is None:
        st.error(message)
        st.stop()

    score = data.get("overall_score", 0)
    try:
        score = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        score = 0

    st.metric("Overall resume score", f"{score}/100")
    st.progress(score / 100)
    st.write(data.get("summary", ""))

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("💪 Strengths")
        for item in data.get("strengths", []):
            st.write(f"- {item}")
    with g2:
        st.subheader("⚠️ Weaknesses")
        for item in data.get("weaknesses", []):
            st.write(f"- {item}")

    if data.get("missing_skills"):
        st.subheader("🧩 Missing skills / keywords")
        st.write(", ".join(data["missing_skills"]))

    st.subheader("🛠️ Suggestions")
    for item in data.get("suggestions", []):
        st.write(f"- {item}")

    if data.get("improved_summary"):
        st.subheader("✨ Suggested profile summary")
        st.code(data["improved_summary"], language=None)  # has a copy button

    if message:
        st.caption(message)
