import streamlit as st
from pypdf import PdfReader
from docx import Document
import re

st.set_page_config(
    page_title="AI Resume Screening System",
    page_icon="📄",
    layout="wide"
)

st.title("🤖 AI Resume Screening System")
st.write("Upload your resume and get a detailed resume analysis.")


# -----------------------------
# EXTRACT TEXT FROM PDF
# -----------------------------
def extract_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


# -----------------------------
# EXTRACT TEXT FROM DOCX
# -----------------------------
def extract_docx(uploaded_file):
    document = Document(uploaded_file)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


# -----------------------------
# EXTRACT RESUME TEXT
# -----------------------------
def extract_resume(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_pdf(uploaded_file)

    if uploaded_file.name.lower().endswith(".docx"):
        return extract_docx(uploaded_file)

    return ""


# -----------------------------
# CHECK CONTACT DETAILS
# -----------------------------
def check_email(text):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return bool(re.search(pattern, text))


def check_phone(text):
    pattern = r"(\+91[\s-]?)?[6-9]\d{9}"
    return bool(re.search(pattern, text))


def check_linkedin(text):
    return "linkedin.com" in text.lower()


def check_github(text):
    return "github.com" in text.lower()


# -----------------------------
# CHECK RESUME SECTIONS
# -----------------------------
def check_section(text, keywords):
    text = text.lower()

    return any(
        keyword in text
        for keyword in keywords
    )


# -----------------------------
# SKILLS DATABASE
# -----------------------------
SKILLS = [
    "python",
    "java",
    "c++",
    "c",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "machine learning",
    "deep learning",
    "data science",
    "data analysis",
    "artificial intelligence",
    "numpy",
    "pandas",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "fastapi",
    "flask",
    "django",
    "html",
    "css",
    "javascript",
    "react",
    "node.js",
    "docker",
    "aws",
    "azure",
    "git",
    "github",
    "power bi",
    "tableau",
    "excel"
]


# -----------------------------
# FIND SKILLS
# -----------------------------
def find_skills(text):
    text = text.lower()
    found = []

    for skill in SKILLS:
        if skill in text:
            found.append(skill)

    return found


# -----------------------------
# JOB DESCRIPTION ANALYSIS
# -----------------------------
def analyse_job_match(resume_text, job_description):
    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_description)

    matched = [
        skill
        for skill in job_skills
        if skill in resume_skills
    ]

    missing = [
        skill
        for skill in job_skills
        if skill not in resume_skills
    ]

    if len(job_skills) == 0:
        score = 0
    else:
        score = round(
            len(matched) / len(job_skills) * 100,
            2
        )

    return score, matched, missing


# -----------------------------
# MAIN RESUME ANALYSIS
# -----------------------------
def analyse_resume(text):
    text_lower = text.lower()
    score = 0
    results = {}
    suggestions = []

    # Email
    results["Email"] = check_email(text)
    if results["Email"]:
        score += 5
    else:
        suggestions.append(
            "Add a professional email address."
        )

    # Phone
    results["Phone"] = check_phone(text)
    if results["Phone"]:
        score += 5
    else:
        suggestions.append(
            "Add a valid phone number."
        )

    # LinkedIn
    results["LinkedIn"] = check_linkedin(text)
    if results["LinkedIn"]:
        score += 5
    else:
        suggestions.append(
            "Add your LinkedIn profile URL."
        )

    # GitHub
    results["GitHub"] = check_github(text)
    if results["GitHub"]:
        score += 5
    else:
        suggestions.append(
            "Add your GitHub profile if you have technical projects."
        )

    # Summary
    results["Professional Summary"] = check_section(
        text_lower,
        ["summary", "professional summary", "profile", "objective"]
    )

    if results["Professional Summary"]:
        score += 10
    else:
        suggestions.append(
            "Add a professional summary or career objective."
        )

    # Education
    results["Education"] = check_section(
        text_lower,
        ["education", "university", "college", "bachelor", "master"]
    )

    if results["Education"]:
        score += 10
    else:
        suggestions.append(
            "Add your education details."
        )

    # Experience
    results["Experience"] = check_section(
        text_lower,
        ["experience", "work experience", "internship", "employment"]
    )

    if results["Experience"]:
        score += 15
    else:
        suggestions.append(
            "Add internship or work experience."
        )

    # Projects
    results["Projects"] = check_section(
        text_lower,
        ["project", "projects", "academic project"]
    )

    if results["Projects"]:
        score += 15
    else:
        suggestions.append(
            "Add relevant projects with technologies and outcomes."
        )

    # Skills
    detected_skills = find_skills(text)

    results["Skills"] = detected_skills

    if len(detected_skills) >= 8:
        score += 15
    elif len(detected_skills) >= 4:
        score += 10
    elif len(detected_skills) > 0:
        score += 5
    else:
        suggestions.append(
            "Add a dedicated technical skills section."
        )

    # Certifications
    results["Certifications"] = check_section(
        text_lower,
        ["certification", "certifications", "certificate"]
    )

    if results["Certifications"]:
        score += 5
    else:
        suggestions.append(
            "Add relevant certifications if available."
        )

    # Resume length
    word_count = len(text.split())
    results["Word Count"] = word_count

    if 300 <= word_count <= 1200:
        score += 10
    elif word_count < 300:
        suggestions.append(
            "Your resume may be too short. Add more relevant details."
        )
    else:
        suggestions.append(
            "Your resume may be too long. Keep it concise."
        )

    # Action words
    action_words = [
        "developed",
        "created",
        "designed",
        "implemented",
        "improved",
        "managed",
        "built",
        "analysed",
        "analyzed",
        "led"
    ]

    action_count = sum(
        1
        for word in action_words
        if word in text_lower
    )

    results["Action Words"] = action_count

    if action_count >= 3:
        score += 5
    else:
        suggestions.append(
            "Use stronger action words such as Developed, Built, "
            "Implemented, Designed, or Improved."
        )

    return min(score, 100), results, suggestions


# -----------------------------
# STATUS
# -----------------------------
def get_status(score):
    if score >= 80:
        return "EXCELLENT"
    elif score >= 65:
        return "GOOD"
    elif score >= 45:
        return "AVERAGE"
    return "POOR"


# -----------------------------
# USER INTERFACE
# -----------------------------
uploaded_file = st.file_uploader(
    "📤 Upload Resume",
    type=["pdf", "docx"]
)

job_description = st.text_area(
    "💼 Paste Job Description (Optional)",
    placeholder="Paste the complete job description here...",
    height=200
)


if uploaded_file is None:
    st.info("👆 Please upload your resume to start analysis.")

else:
    try:
        resume_text = extract_resume(uploaded_file)

        if not resume_text.strip():
            st.error(
                "Could not extract text from this resume."
            )

        else:
            resume_score, results, suggestions = (
                analyse_resume(resume_text)
            )

            # Job description score
            if job_description.strip():
                job_score, matched, missing = (
                    analyse_job_match(
                        resume_text,
                        job_description
                    )
                )

                # Final combined score
                final_score = round(
                    resume_score * 0.6 +
                    job_score * 0.4
                )

            else:
                job_score = None
                matched = []
                missing = []
                final_score = resume_score

            status = get_status(final_score)

            # -----------------------------
            # SCORE DISPLAY
            # -----------------------------
            st.divider()

            st.subheader("📊 Resume Score")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Overall Score",
                f"{final_score}/100"
            )

            col2.metric(
                "Resume Quality",
                f"{resume_score}/100"
            )

            if job_score is not None:
                col3.metric(
                    "Job Match",
                    f"{job_score}%"
                )
            else:
                col3.metric(
                    "Job Match",
                    "Not Provided"
                )

            st.progress(final_score / 100)

            # -----------------------------
            # STATUS
            # -----------------------------
            if status == "EXCELLENT":
                st.success(
                    "🌟 EXCELLENT RESUME"
                )

            elif status == "GOOD":
                st.success(
                    "✅ GOOD RESUME"
                )

            elif status == "AVERAGE":
                st.warning(
                    "🟡 AVERAGE RESUME"
                )

            else:
                st.error(
                    "❌ POOR RESUME - NEEDS IMPROVEMENT"
                )

            # -----------------------------
            # RESUME CHECKLIST
            # -----------------------------
            st.divider()
            st.subheader("🔍 Resume Analysis")

            analysis_columns = st.columns(2)

            items = [
                "Email",
                "Phone",
                "LinkedIn",
                "GitHub",
                "Professional Summary",
                "Education",
                "Experience",
                "Projects",
                "Certifications"
            ]

            for index, item in enumerate(items):
                column = analysis_columns[index % 2]

                if results[item]:
                    column.success(f"✅ {item} Found")
                else:
                    column.error(f"❌ {item} Missing")

            # -----------------------------
            # SKILLS
            # -----------------------------
            st.divider()
            st.subheader("🛠️ Skills Detected")

            if results["Skills"]:
                st.write(", ".join(results["Skills"]))
            else:
                st.warning("No known technical skills detected.")

            st.write(
                f"**Resume Word Count:** "
                f"{results['Word Count']}"
            )

            st.write(
                f"**Action Words Found:** "
                f"{results['Action Words']}"
            )

            # -----------------------------
            # JOB MATCH
            # -----------------------------
            if job_description.strip():
                st.divider()
                st.subheader("💼 Job Description Match")

                left, right = st.columns(2)

                with left:
                    st.success("✅ Matched Skills")

                    if matched:
                        for skill in matched:
                            st.write(f"• {skill}")
                    else:
                        st.write(
                            "No major skills matched."
                        )

                with right:
                    st.error("❌ Missing Skills")

                    if missing:
                        for skill in missing:
                            st.write(f"• {skill}")
                    else:
                        st.write(
                            "No major skills are missing."
                        )

            # -----------------------------
            # SUGGESTIONS
            # -----------------------------
            st.divider()
            st.subheader("💡 Recommended Changes")

            if missing:
                suggestions.append(
                    "For this job, consider adding these skills "
                    "if you genuinely know them: "
                    + ", ".join(missing)
                )

            if suggestions:
                for suggestion in suggestions:
                    st.info(f"💡 {suggestion}")
            else:
                st.success(
                    "Your resume looks well structured!"
                )

            # -----------------------------
            # EXPANDER
            # -----------------------------
            with st.expander("View Extracted Resume Text"):
                st.text(resume_text)

    except Exception as error:
        st.error(f"Error while analyzing resume: {error}")
