from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import shutil
import os
import tempfile

app = FastAPI()
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


def calculate_skill_match(resume_text, required_skills):
    text = resume_text.lower()
    found = [s for s in required_skills if s.lower() in text]
    missing = [s for s in required_skills if s.lower() not in text]
    score = round(len(found) / len(required_skills) * 100, 2) if required_skills else 0
    return score, found, missing


def semantic_similarity(resume, job_description):
    vectors = model.encode([resume, job_description])
    similarity = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return round(float(similarity) * 100, 2)


@app.post("/screen")
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not resume.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    suffix = os.path.splitext(resume.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix
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

        job_skills = [
            "python",
            "machine learning",
            "sql",
            "tensorflow",
            "pandas"
        ]

        semantic_score = semantic_similarity(
            resume_text, job_description
        )

        skill_score, found, missing = calculate_skill_match(
            resume_text, job_skills
        )

        return {
            "candidate": resume.filename,
            "semantic_score": semantic_score,
            "skill_match_score": skill_score,
            "found_skills": found,
            "missing_skills": missing
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        await resume.close()
