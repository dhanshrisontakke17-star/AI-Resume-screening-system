import streamlit as st
import random

st.title("AI Resume Screening System")

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if uploaded_file is not None:
    score = random.randint(50, 100)

    st.success(f"Uploaded: {uploaded_file.name}")
    st.write("Resume Score: 85%")
    st.write(f"Resume Score: {score}%")

    if score >= 85:
        st.success("✅ Good Resume")
    elif score >= 70:
        st.warning("🟡 Average Resume")
    else:
        st.error("❌ Poor Resume")

else:
    st.warning("Please upload your resume.")
    model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_pdf(path):
    reader = PdfReader(path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def extract_docx(path):
    document = Document(path)
    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_resume(path):
    if path.lower().endswith(".pdf"):
        return extract_pdf(path)

    elif path.lower().endswith(".docx"):
        return extract_docx(path)

    else:
        raise ValueError("Only PDF and DOCX files are supported")


def get_skills(text):
    skills = [
        "python",
        "java",
        "c++",
        "sql",
        "mysql",
        "mongodb",
        "machine learning",
        "deep learning",
        "data analysis",
        "data science",
        "pandas",
        "numpy",
        "tensorflow",
        "pytorch",
        "fastapi",
        "django",
        "flask",
        "html",
        "css",
        "javascript",
        "react",
        "node.js",
        "docker",
        "aws",
        "git"
    ]

    text = text.lower()

    found_skills = []

    for skill in skills:
        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills


def calculate_skill_match(resume_text, job_description):
    resume_skills = get_skills(resume_text)
    job_skills = get_skills(job_description)

    matched = []
    missing = []

    for skill in job_skills:
        if skill in resume_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    if len(job_skills) > 0:
        score = (len(matched) / len(job_skills)) * 100
    else:
        score = 0

    return round(score, 2), matched, missing


def semantic_similarity(resume_text, job_description):
    embeddings = model.encode(
        [resume_text, job_description]
    )

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return round(float(similarity) * 100, 2)


def get_status(score):
    if score >= 70:
        return "GOOD"
    elif score >= 40:
        return "AVERAGE"
    else:
        return "BAD"


def get_suggestions(missing_skills, final_score):
    suggestions = []

    if final_score < 40:
        suggestions.append(
            "Your resume needs significant improvement for this job."
        )

    elif final_score < 70:
        suggestions.append(
            "Your resume partially matches the job description."
        )

    else:
        suggestions.append(
            "Your resume is a good match for this job."
        )

    if missing_skills:
        suggestions.append(
            "Add these skills if you actually know them: " +
            ", ".join(missing_skills)
        )

    return suggestions


@app.post("/screen")
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):

    if not resume.filename:
        raise HTTPException(
            status_code=400,
            detail="Please upload a resume"
        )

    if not resume.filename.lower().endswith(
        (".pdf", ".docx")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )

    suffix = os.path.splitext(resume.filename)[1]

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    file_path = temp_file.name
    temp_file.close()

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)

        resume_text = extract_resume(file_path)

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume"
            )

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

        final_score = round(
            (semantic_score * 0.6) +
            (skill_score * 0.4),
            2
        )

        status = get_status(final_score)

        suggestions = get_suggestions(
            missing_skills,
            final_score
        )

        return {
            "candidate": resume.filename,
            "resume_score": final_score,
            "status": status,
            "semantic_score": semantic_score,
            "skill_score": skill_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "suggestions": suggestions
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

        await resume.close()
