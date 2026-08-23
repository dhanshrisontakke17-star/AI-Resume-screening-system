import streamlit as st
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import tempfile


st.set_page_config(
    page_title="AI Resume Screening System",
    layout="wide"
)

st.title("AI Resume Screening System")

# Load model
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


model = load_model()


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

    elif path.lower().endswith(".docx"):
        return extract_docx(path)

    return ""


def get_skills(text):
    skills = [
        "python",
        "java",
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
        "docker",
        "aws",
        "git"
    ]

    text = text.lower()

    return [
        skill
        for skill in skills
        if skill in text
    ]


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

    if len(job_skills) == 0:
        score = 0
    else:
        score = (len(matched) / len(job_skills)) * 100

    return round(score, 2), matched, missing


def semantic_similarity(resume_text, job_description):
    embeddings = model.encode(
        [resume_text, job_description]
    )

    resume_vector = embeddings[0]
    job_vector = embeddings[1]

    dot_product = np.dot(
        resume_vector,
        job_vector
    )

    resume_norm = np.linalg.norm(resume_vector)
    job_norm = np.linalg.norm(job_vector)

    if resume_norm == 0 or job_norm == 0:
        return 0

    similarity = dot_product / (
        resume_norm * job_norm
    )

    return round(float(similarity) * 100, 2)


def get_status(score):
    if score >= 70:
        return "GOOD"
    elif score >= 40:
        return "AVERAGE"
    else:
        return "BAD"


def get_suggestions(score, missing_skills):
    suggestions = []

    if score >= 70:
        suggestions.append(
            "Your resume is a good match for this job."
        )

    elif score >= 40:
        suggestions.append(
            "Your resume partially matches this job."
        )

    else:
        suggestions.append(
            "Your resume needs improvement for this job."
        )

    if missing_skills:
        suggestions.append(
            "Add these skills only if you actually have them: "
            + ", ".join(missing_skills)
        )

    return suggestions


uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx"]
)

job_description = st.text_area(
    "Enter Job Description",
    height=200
)


if uploaded_file is None:
    st.info("Please upload your resume.")

elif not job_description.strip():
    st.warning("Please enter the job description.")

else:
    suffix = os.path.splitext(uploaded_file.name)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        file_path = temp_file.name

    try:
        resume_text = extract_resume(file_path)

        if not resume_text.strip():
            st.error("Could not extract text from the resume.")

        else:
            semantic_score = semantic_similarity(
                resume_text,
                job_description
            )

            skill_score, matched, missing = (
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
                final_score,
                missing
            )

            st.subheader("Resume Analysis")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Resume Score",
                f"{final_score}%"
            )

            col2.metric(
                "Semantic Match",
                f"{semantic_score}%"
            )

            col3.metric(
                "Skill Match",
                f"{skill_score}%"
            )

            if status == "GOOD":
                st.success(f"Result: {status}")

            elif status == "AVERAGE":
                st.warning(f"Result: {status}")

            else:
                st.error(f"Result: {status}")

            st.subheader("Matched Skills")

            if matched:
                st.write(", ".join(matched))
            else:
                st.write("No matching skills found.")

            st.subheader("Missing Skills")

            if missing:
                st.write(", ".join(missing))
            else:
                st.success("No important skills are missing.")

            st.subheader("Suggestions")

            for suggestion in suggestions:
                st.write("• " + suggestion)

    except Exception as e:
        st.error(f"Error: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
