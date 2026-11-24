"""Streamlit Web Application for Automated Resume Screening.

Deployable on Streamlit Community Cloud and runnable locally via:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import pandas as pd
import streamlit as st

# Import core project modules
from src.resume_screening.extraction.extractor import DocumentExtractor
from src.resume_screening.matching.matcher import SkillMatcher
from src.resume_screening.matching.scorer import ResumeScorer
from src.resume_screening.schemas import ExtractedResume, JobDescription

# -----------------------------------------------------------------------------
# Configuration and Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Automated Resume Screening Tool",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT_DIR = Path(__file__).resolve().parent
SAMPLE_RESUMES_DIR = ROOT_DIR / "resumes" / "sample"
JOB_DESCRIPTIONS_FILE = ROOT_DIR / "data" / "job_descriptions.json"


@st.cache_data
def load_sample_jobs() -> List[dict]:
    """Loads default job profiles from data/job_descriptions.json."""
    if JOB_DESCRIPTIONS_FILE.exists():
        try:
            with open(JOB_DESCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


sample_jobs = load_sample_jobs()

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("Automated Resume Screening Tool")
st.markdown(
    "Intelligent resume parsing, skill ontology matching, multi-factor scoring, and candidate ranking. "
    "Designed as a decision-support aid for recruitment teams."
)

# -----------------------------------------------------------------------------
# Sidebar: Job Profile Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("1. Target Job Profile")

    job_options = [j["title"] for j in sample_jobs] + ["Custom Job Profile"]
    selected_option = st.selectbox("Select Role", options=job_options)

    if selected_option != "Custom Job Profile":
        job_data = next((j for j in sample_jobs if j["title"] == selected_option), None)
        default_title = job_data.get("title", "")
        default_desc = job_data.get("description", "")
        default_exp = float(job_data.get("experience_years_required", 3.0))
        default_req = ", ".join(job_data.get("required_skills", []))
        default_pref = ", ".join(job_data.get("preferred_skills", []))
    else:
        default_title = "Senior Python Developer"
        default_desc = "Seeking a senior engineer proficient in Python, APIs, and cloud infrastructure."
        default_exp = 4.0
        default_req = "Python, FastAPI, Docker, SQL"
        default_pref = "AWS, Kubernetes, CI/CD"

    job_title = st.text_input("Job Title", value=default_title)
    job_experience = st.number_input(
        "Required Experience (Years)", min_value=0.0, max_value=25.0, value=default_exp, step=0.5
    )
    job_required = st.text_area("Required Skills (comma-separated)", value=default_req, height=80)
    job_preferred = st.text_area("Preferred Skills (comma-separated)", value=default_pref, height=80)
    job_description = st.text_area("Job Description", value=default_desc, height=140)

    st.markdown("---")
    st.header("2. Resume Source")
    use_sample_data = st.checkbox("Use Built-in Synthetic Resumes (5 profiles)", value=True)
    uploaded_files = st.file_uploader(
        "Or Upload Candidate Resumes (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

# -----------------------------------------------------------------------------
# Processing Functions
# -----------------------------------------------------------------------------
def parse_and_score(
    files_to_process: List[Path],
    job: JobDescription,
    scorer: ResumeScorer,
    matcher: SkillMatcher,
):
    extracted_resumes: List[ExtractedResume] = []
    progress_bar = st.progress(0, text="Parsing resumes...")

    for idx, path in enumerate(files_to_process):
        text = DocumentExtractor.extract_text(str(path))
        clean_text = DocumentExtractor.clean_text(text)
        cand_name = DocumentExtractor.extract_candidate_name(text, path.name)
        exp_years = DocumentExtractor.estimate_experience_years(text)
        skills = matcher.extract_skills_from_text(clean_text)

        extracted = ExtractedResume(
            filename=path.name,
            candidate_name=cand_name,
            estimated_experience_years=exp_years,
            extracted_skills=skills,
            clean_text=clean_text,
            raw_text=text,
        )
        extracted_resumes.append(extracted)
        progress_bar.progress((idx + 1) / len(files_to_process), text=f"Parsed {path.name}")

    progress_bar.empty()
    ranked_candidates = scorer.rank_candidates(extracted_resumes, job)
    return ranked_candidates


# -----------------------------------------------------------------------------
# Main Action
# -----------------------------------------------------------------------------
start_btn = st.button("Run Screening & Candidate Ranking", type="primary", use_container_width=True)

if start_btn:
    req_skills_list = [s.strip() for s in job_required.split(",") if s.strip()]
    pref_skills_list = [s.strip() for s in job_preferred.split(",") if s.strip()]

    if not job_title.strip() or not job_description.strip():
        st.error("Please provide both a Job Title and a Job Description.")
        st.stop()

    if not req_skills_list:
        st.error("Please specify at least one required skill.")
        st.stop()

    job_spec = JobDescription(
        id="JOB-CUSTOM",
        title=job_title.strip(),
        description=job_description.strip(),
        experience_years_required=job_experience,
        required_skills=req_skills_list,
        preferred_skills=pref_skills_list,
    )

    matcher = SkillMatcher()
    scorer = ResumeScorer(skill_matcher=matcher)

    candidate_paths: List[Path] = []
    temp_dir_obj = None

    if uploaded_files:
        temp_dir_obj = TemporaryDirectory()
        temp_dir_path = Path(temp_dir_obj.name)
        for upload in uploaded_files:
            file_dest = temp_dir_path / upload.name
            file_dest.write_bytes(upload.getvalue())
            candidate_paths.append(file_dest)

    if use_sample_data and SAMPLE_RESUMES_DIR.exists():
        sample_files = sorted(SAMPLE_RESUMES_DIR.glob("*.txt"))
        candidate_paths.extend(sample_files)

    if not candidate_paths:
        st.warning("No resumes selected. Please upload files or check 'Use Built-in Synthetic Resumes'.")
        st.stop()

    with st.spinner("Evaluating candidate proficiencies and computing multi-factor scores..."):
        ranked_scores = parse_and_score(candidate_paths, job_spec, scorer, matcher)
        st.session_state["screening_results"] = ranked_scores
        st.session_state["target_job"] = job_spec

    if temp_dir_obj:
        temp_dir_obj.cleanup()

# -----------------------------------------------------------------------------
# Display Results
# -----------------------------------------------------------------------------
if "screening_results" in st.session_state:
    results = st.session_state["screening_results"]
    job_spec = st.session_state["target_job"]

    st.markdown("---")
    st.subheader(f"Screening Scorecard: {job_spec.title}")

    # Top KPI Metrics
    total = len(results)
    strong = sum(1 for c in results if c.fit_category == "Strong Match")
    moderate = sum(1 for c in results if c.fit_category == "Moderate Match")
    weak = sum(1 for c in results if c.fit_category == "Weak Match")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Candidates", total)
    kpi2.metric("Strong Matches", strong)
    kpi3.metric("Moderate Matches", moderate)
    kpi4.metric("Weak Matches", weak)

    # Summary Table
    rows = []
    total_req_count = len(job_spec.required_skills)
    for c in results:
        rows.append(
            {
                "Rank": c.rank,
                "Candidate Name": c.candidate_name,
                "Filename": c.filename,
                "Total Score (%)": c.total_score,
                "Fit Category": c.fit_category,
                "Required Skills": f"{len(c.skill_breakdown.matched_required_skills)}/{total_req_count}",
                "Est. Experience (Yrs)": f"{c.estimated_experience_years:.1f}" if c.estimated_experience_years is not None else "N/A",
                "TF-IDF Score (max 25)": c.tfidf_similarity_score,
            }
        )
    df_results = pd.DataFrame(rows)

    st.dataframe(df_results, use_container_width=True, hide_index=True)

    # Detailed Candidate Breakdowns
    st.markdown("### Candidate Competency Breakdown")
    for c in results:
        with st.expander(f"Rank {c.rank}: {c.candidate_name} ({c.fit_category} - {c.total_score}%)"):
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Matched Required Skills:**")
                if c.skill_breakdown.matched_required_skills:
                    st.success(", ".join(c.skill_breakdown.matched_required_skills))
                else:
                    st.write("None detected")

                st.markdown("**Missing Required Skills:**")
                if c.skill_breakdown.missing_required_skills:
                    st.error(", ".join(c.skill_breakdown.missing_required_skills))
                else:
                    st.write("None missing")

            with col_b:
                st.markdown("**Matched Preferred Skills:**")
                if c.skill_breakdown.matched_preferred_skills:
                    st.info(", ".join(c.skill_breakdown.matched_preferred_skills))
                else:
                    st.write("None detected")

                st.markdown("**Scoring Factor Breakdown (100 pts max):**")
                st.write(f"- Required Skills (max 40): **{c.required_skill_score}**")
                st.write(f"- Preferred Skills (max 20): **{c.preferred_skill_score}**")
                st.write(f"- TF-IDF Text Similarity (max 25): **{c.tfidf_similarity_score}**")
                st.write(f"- Experience Alignment (max 15): **{c.experience_score}**")

    # CSV Download
    csv_data = df_results.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Download Screening Report (CSV)",
        data=csv_data,
        file_name="candidate_screening_report.csv",
        mime="text/csv",
    )

    st.caption(
        "Ethical Notice: Automated rankings quantify text overlap and listed skills. "
        "Scores assist recruiter review and should not replace human hiring judgment."
    )
