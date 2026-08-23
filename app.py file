from pypdf import PdfReader
from docx import Document


def extract_pdf(path):
    reader = PdfReader(path)

    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return text


def extract_docx(path):
    document = Document(path)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


def extract_resume(path):
    if path.lower().endswith(".pdf"):
        return extract_pdf(path)

    if path.lower().endswith(".docx"):
        return extract_docx(path)

    raise ValueError("Only PDF and DOCX files are supported")
  def calculate_skill_match(resume_text, required_skills):
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

    return score, found, missing


job_skills = [
    "python",
    "machine learning",
    "sql",
    "tensorflow",
    "pandas"
]

score, found, missing = calculate_skill_match(
    resume_text,
    job_skills
)

print("Score:", score)
print("Found:", found)
print("Missing:", missing)
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")


def semantic_similarity(resume, job_description):
    resume_vector = model.encode([resume])
    job_vector = model.encode([job_description])

    similarity = cosine_similarity(
        resume_vector,
        job_vector
    )[0][0]

    return round(similarity * 100, 2)
  from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os

app = FastAPI()


@app.post("/screen")
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    file_path = f"temp_{resume.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    try:
        resume_text = extract_resume(file_path)

        similarity = semantic_similarity(
            resume_text,
            job_description
        )

        return {
            "candidate": resume.filename,
            "semantic_score": similarity
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
