from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import os
import shutil
import tempfile


app = FastAPI(title="AI Resume Screening API")


# Load the semantic model once when the application starts
model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_pdf(path):
    """Extract text from a PDF file."""
    reader = PdfReader(path)

    text = ""

    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"

    return text


def extract_docx(path):
    """Extract text from a DOCX file."""
    document = Document(path)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


def extract_resume(path):
    """Extract text based on the file extension."""
    if path.lower().endswith(".pdf"):
        return extract_pdf(path)

    elif path.lower().endswith(".docx"):
        return extract_docx(path)

    raise ValueError("Only PDF and DOCX files are supported")


def calculate_skill_match(resume_text, required_skills):
    """Calculate keyword-based skill matching score."""
    resume_text = resume_text.lower()

    found = []
    missing = []

    for skill in required_skills:
        if skill.lower() in resume_text:
            found.append(skill)
        else:
            missing.append(skill)

    if required_skills:
        score = (len(found) / len(required_skills)) * 100
    else:
        score = 0

    return round(score, 2), found, missing


def semantic_similarity(resume, job_description):
    """Calculate semantic similarity between resume and job description."""

    resume_vector = model.encode([resume])
    job_vector = model.encode([job_description])

    similarity = cosine_similarity(
        resume_vector,
        job_vector
    )[0][0]

    return round(float(similarity) * 100, 2)


@app.get("/")
def home():
    return {
        "message": "AI Resume Screening API is running"
    }


@app.post("/screen")
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    # Check file type
    if not resume.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    # Create a temporary file
    suffix = os.path.splitext(resume.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        file_path = temp_file.name

        shutil.copyfileobj(
            resume.file,
            temp_file
        )

    try:
        # Extract resume text
        resume_text = extract_resume(file_path)

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the resume"
            )

        # Calculate semantic similarity
        similarity = semantic_similarity(
            resume_text,
            job_description
        )

        # Example skills
        job_skills = [
            "python",
            "machine learning",
            "sql",
            "tensorflow",
            "pandas"
        ]

        # Calculate skill match
        skill_score, found_skills, missing_skills = (
            calculate_skill_match(
                resume_text,
                job_skills
            )
        )

        return {
            "candidate": resume.filename,
            "semantic_score": similarity,
            "skill_match_score": skill_score,
            "found_skills": found_skills,
            "missing_skills": missing_skills
        }

    finally:
        # Delete temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

        await resume.close()
        



    
