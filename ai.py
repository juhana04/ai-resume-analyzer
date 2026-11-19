"""
ai.py - the AI part: sends the resume (and job description) to Google Gemini
and gets back a structured review as JSON.

If one Gemini model is busy, it automatically tries backup models.
"""

import json
import os
import time

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from the .env file

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def key_loaded():
    return bool(os.getenv("GEMINI_API_KEY"))


def build_prompt(resume_text, jd_text):
    jd_part = (
        f"JOB DESCRIPTION:\n{jd_text[:6000]}\n"
        if jd_text.strip()
        else "JOB DESCRIPTION: (none given - do a general review for a fresher software/CSE role)\n"
    )
    return f"""You are an experienced technical recruiter and resume coach.
Review the resume below{' against the job description' if jd_text.strip() else ''}.
Be honest, specific and practical. Never invent experience the candidate does not have.

Reply with ONLY valid JSON (no markdown, no extra text) using exactly these keys:
{{
  "overall_score": <integer 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "strengths": ["<short point>", "..."],
  "weaknesses": ["<short point>", "..."],
  "missing_skills": ["<skill or keyword from the job description that is absent>", "..."],
  "suggestions": ["<specific, actionable improvement>", "..."],
  "improved_summary": "<a rewritten 3-4 line profile summary using only facts from the resume>"
}}

{jd_part}
RESUME:
{resume_text[:12000]}
"""


def parse_json(text):
    """Pull the JSON object out of the model's reply."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found in the AI reply")
    return json.loads(text[start : end + 1])


def _candidate_models(client):
    """Ask Google which flash models this key can use (backup models)."""
    names = []
    try:
        for m in client.models.list():
            name = (m.name or "").replace("models/", "")
            low = name.lower()
            actions = getattr(m, "supported_actions", None) or ["generateContent"]
            if "generateContent" not in actions or "flash" not in low:
                continue
            if any(x in low for x in ("image", "tts", "live", "audio",
                                      "embedding", "robotics", "computer")):
                continue
            names.append(name)
    except Exception:
        pass
    return names[:6]


def analyze(resume_text, jd_text=""):
    """Returns (result_dict, message). On success message is ''; on failure result is None."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, (
            "No GEMINI_API_KEY found. Open the .env file, add "
            "GEMINI_API_KEY=your_key, save, and restart the app."
        )

    from google import genai

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(resume_text, jd_text)

    queue, tried, expanded, last_error = [GEMINI_MODEL], set(), False, ""

    while queue:
        model = queue.pop(0)
        if model in tried:
            continue
        tried.add(model)

        for attempt in range(2):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = (getattr(response, "text", None) or "").strip()
                if not text:
                    last_error = "empty answer"
                    break
                data = parse_json(text)
                note = "" if model == GEMINI_MODEL else f"(Answered using {model} because {GEMINI_MODEL} was busy.)"
                return data, note
            except (ValueError, json.JSONDecodeError) as error:
                last_error = f"could not read the AI reply ({error})"
                if attempt == 0:
                    continue  # ask once more
                break
            except Exception as error:
                msg = str(error)
                last_error = msg
                if any(k in msg for k in ("API_KEY", "API key", "401", "403", "PERMISSION")):
                    return None, f"Your API key was rejected: {msg}"
                if ("503" in msg or "UNAVAILABLE" in msg) and attempt == 0:
                    time.sleep(2)
                    continue
                break

        if not expanded:
            expanded = True
            queue.extend(_candidate_models(client))

    if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
        return None, "⏳ Free-tier limit reached. Please wait about a minute and try again."
    return None, (
        "Google's AI servers are busy right now and every model I tried failed. "
        f"Please wait a minute and try again.\n\nLast error: {last_error}"
    )
