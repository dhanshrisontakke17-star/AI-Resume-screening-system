from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import shutil
import os
import tempfile
import re

app = FastAPI(title="AI Resume Screener")

model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_pdf(path):
    return "\n".join(
        page.extract_text() or ""
        for page in PdfReader(path).pages
    )


def extract_docx(path):
    return "\n".join(
        p.text for p in Document(path).paragraphs
    )


def extract_resume(path):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return extract_pdf(path)

    if ext == ".docx":
        return extract_docx(path)

    raise ValueError("Only PDF and DOCX files are supported")


def semantic_similarity(resume, job_description):
    vectors = model.encode([resume, job_description])

    score = cosine_similarity(
        [vectors[0]],
        [vectors[1]]
    )[0][0]

    return round(float(score) * 100, 2)


def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.]{2,}\b", text.lower())

    stop_words = {
        "and", "the", "with", "for", "are", "this",
        "that", "from", "have", "will", "you", "your",
        "our", "job", "role", "work", "team", "years",
        "experience", "candidate", "required", "skills"
    }

    return list(set(
        word for word in words
        if word not in stop_words
    ))


def calculate_skill_match(resume_text, job_description):
    resume_words = set(extract_keywords(resume_text))
    job_words = set(extract_keywords(job_description))

    matched = resume_words.intersection(job_words)
    missing = job_words - resume_words

    if job_words:
        score = (len(matched) / len(job_words)) * 100
    else:
        score = 0

    return round(score, 2), sorted(matched), sorted(missing)


def get_resume_status(score):
    if score >= 75:
        return "GOOD"
    elif score >= 50:
        return "AVERAGE"
    return "BAD"


def get_suggestions(
    semantic_score,
    skill_score,
    missing_skills
):
    suggestions = []

    if semantic_score < 50:
        suggestions.append(
            "Resume content does not match the job description well. "
            "Add more relevant experience and responsibilities."
        )

    if skill_score < 50:
        suggestions.append(
            "Add relevant skills mentioned in the job description."
        )

    if missing_skills:
        suggestions.append(
            "Consider adding these relevant keywords if you have "
            "experience with them: " +
            ", ".join(missing_skills[:10])
        )

    if semantic_score >= 75 and skill_score >= 60:
        suggestions.append(
            "Your resume matches the job description well."
        )

    return suggestions


@app.post("/screen")
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not resume.filename.lower().endswith(
        (".pdf", ".docx")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    suffix = os.path.splitext(resume.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp:
        file_path = temp.name
        shutil.copyfileobj(resume.file, temp)

    try:
        resume_text = extract_resume(file_path)

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text found in resume"
            )

        # Compare resume with job description
        semantic_score = semantic_similarity(
            resume_text,
            job_description
        )

        skill_score, matched_skills, missing_skills = (
            calculate_skill_match(
                resume_text,
                job_description
            )
        )

        # Final score
        final_score = round(
            semantic_score * 0.6 +
            skill_score * 0.4,
            2
        )

        status = get_resume_status(final_score)

        suggestions = get_suggestions(
            semantic_score,
            skill_score,
            missing_skills
        )

        return {
            "candidate": resume.filename,

            "resume_score": final_score,

            "status": status,

            "semantic_match": semantic_score,

            "keyword_match": skill_score,

            "matched_keywords": matched_skills[:20],

            "missing_keywords": missing_skills[:20],

            "suggestions": suggestions
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

        await resume.close()
