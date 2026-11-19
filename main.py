"""Automated Resume Screening Tool — Application Entry Point.

This CLI/server entry point provides three distinct operational modes:
1. Sample Simulation (`--simulate`, default): Runs an end-to-end batch screening of all synthetic
   candidate resumes against benchmark job descriptions, prints a structured scorecard,
   and writes a JSON report to `outputs/sample_screening_report.json`.
2. API Server (`--serve`): Launches the FastAPI backend with Uvicorn on localhost:8000.
3. Single Resume Analysis (`--file PATH`): Parses and scores an individual resume.

Usage:
    python main.py                      # Runs the sample simulation
    python main.py --simulate           # Explicit simulation run
    python main.py --serve              # Starts the FastAPI server on port 8000
    python main.py --file resumes/sample/sarah_chen_senior_ai_engineer.txt
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.resume_screening.schemas import JobDescription, ExtractedResume
from src.resume_screening.extraction.extractor import DocumentExtractor
from src.resume_screening.matching.matcher import SkillMatcher
from src.resume_screening.matching.scorer import ResumeScorer


def run_sample_simulation(job_id: str = "JD-001", output_dir: str = "outputs"):
    """Executes a complete batch screening simulation on synthetic resumes."""
    print("=" * 80)
    print("      AUTOMATED RESUME SCREENING TOOL — BATCH SIMULATION ENGINE")
    print("=" * 80)

    # 1. Load Job Description
    job_file = PROJECT_ROOT / "data" / "job_descriptions.json"
    if not job_file.exists():
        print(f"[ERROR] Job descriptions fixture not found at: {job_file}")
        return 1

    with open(job_file, "r", encoding="utf-8") as f:
        job_data = json.load(f)

    target_job = None
    for j in job_data:
        if j.get("id", "").lower() == job_id.lower():
            target_job = JobDescription(**j)
            break

    if not target_job and job_data:
        target_job = JobDescription(**job_data[0])

    print(f"\n[+] TARGET JOB PROFILE: {target_job.title} ({target_job.id})")
    print(f"    Required Experience : {target_job.experience_years_required} years")
    print(f"    Required Skills     : {', '.join(target_job.required_skills)}")
    print(f"    Preferred Skills    : {', '.join(target_job.preferred_skills)}")

    # 2. Ingest & Extract Sample Resumes
    resumes_dir = PROJECT_ROOT / "resumes" / "sample"
    if not resumes_dir.exists():
        print(f"[ERROR] Resumes directory not found at: {resumes_dir}")
        return 1

    matcher = SkillMatcher(str(PROJECT_ROOT / "data" / "skills.json"))
    scorer = ResumeScorer(matcher)

    extracted_resumes = []
    resume_files = sorted(list(resumes_dir.glob("*.txt")) + list(resumes_dir.glob("*.pdf")) + list(resumes_dir.glob("*.docx")))

    print(f"\n[+] INGESTING & PARSING RESUMES ({len(resume_files)} detected)...")
    for r_file in resume_files:
        raw_text = DocumentExtractor.extract_text(str(r_file))
        clean_text = DocumentExtractor.clean_text(raw_text)
        candidate_name = DocumentExtractor.extract_candidate_name(raw_text, r_file.name)
        exp_years = DocumentExtractor.estimate_experience_years(raw_text)
        sections = DocumentExtractor.detect_sections(raw_text)
        skills = matcher.extract_skills_from_text(clean_text)

        extracted = ExtractedResume(
            filename=r_file.name,
            candidate_name=candidate_name,
            raw_text=raw_text,
            clean_text=clean_text,
            extracted_skills=skills,
            estimated_experience_years=exp_years,
            sections_detected=sections
        )
        extracted_resumes.append(extracted)
        exp_desc = f"{exp_years:.1f} yrs exp" if exp_years is not None else "unknown exp"
        print(f"    - Parsed '{r_file.name}' -> {candidate_name} ({exp_desc}, {len(skills)} skills detected)")

    # 3. Score & Rank Resumes
    print("\n[+] SCORING & RANKING CANDIDATES...")
    ranked = scorer.rank_candidates(extracted_resumes, target_job)

    # 4. Display Results in Terminal Table
    print("\n" + "=" * 80)
    print(f"{'RANK':<5} | {'CANDIDATE NAME':<22} | {'SCORE':<7} | {'FIT CATEGORY':<14} | {'REQ SKILLS':<12} | {'EXP (YRS)':<9}")
    print("-" * 80)

    report_records = []
    for c in ranked:
        req_ratio_str = f"{len(c.skill_breakdown.matched_required_skills)}/{len(target_job.required_skills)}"
        exp_str = f"{c.estimated_experience_years:.1f}" if c.estimated_experience_years is not None else "Unknown"
        print(f"{c.rank:<5} | {c.candidate_name:<22} | {c.total_score:>5.1f}% | {c.fit_category:<14} | {req_ratio_str:<12} | {exp_str:<9}")
        report_records.append(c.model_dump())

    print("=" * 80)

    # 5. Export Report
    out_path = PROJECT_ROOT / output_dir
    out_path.mkdir(parents=True, exist_ok=True)
    report_file = out_path / "sample_screening_report.json"

    simulation_output = {
        "job_id": target_job.id,
        "job_title": target_job.title,
        "target_skills": target_job.required_skills,
        "screened_at": datetime.now(timezone.utc).isoformat(),
        "total_screened": len(ranked),
        "rankings": report_records
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(simulation_output, f, indent=2)

    print(f"\n[✓] SIMULATION COMPLETE. Report saved to: {report_file.relative_to(PROJECT_ROOT)}")
    return 0


def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Starts the FastAPI backend using Uvicorn."""
    try:
        import uvicorn
        print(f"Starting FastAPI server on http://{host}:{port} ...")
        print("API Documentation available at: http://localhost:8000/docs")
        uvicorn.run("src.resume_screening.api.app:app", host=host, port=port, reload=reload)
    except ImportError:
        print("[ERROR] 'uvicorn' is not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)


def analyze_single_file(file_path: str, job_id: str = "JD-001"):
    """Parses and scores a single resume file against a job profile."""
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return 1

    job_file = PROJECT_ROOT / "data" / "job_descriptions.json"
    with open(job_file, "r", encoding="utf-8") as f:
        job_data = json.load(f)
    job = JobDescription(**job_data[0])

    matcher = SkillMatcher(str(PROJECT_ROOT / "data" / "skills.json"))
    scorer = ResumeScorer(matcher)

    raw_text = DocumentExtractor.extract_text(str(path))
    clean_text = DocumentExtractor.clean_text(raw_text)
    candidate_name = DocumentExtractor.extract_candidate_name(raw_text, path.name)
    exp_years = DocumentExtractor.estimate_experience_years(raw_text)
    skills = matcher.extract_skills_from_text(clean_text)

    resume = ExtractedResume(
        filename=path.name,
        candidate_name=candidate_name,
        raw_text=raw_text,
        clean_text=clean_text,
        extracted_skills=skills,
        estimated_experience_years=exp_years,
        sections_detected=DocumentExtractor.detect_sections(raw_text)
    )

    score = scorer.score_candidate(resume, job)
    exp_info = f"{score.estimated_experience_years:.1f} years" if score.estimated_experience_years is not None else "Unknown"
    print(f"\nAnalysis for: {score.candidate_name} ({score.filename})")
    print(f"Overall Fit: {score.fit_category} (Score: {score.total_score}%)")
    print(f"Estimated Experience: {exp_info}")
    print(f"TF-IDF Cosine Similarity: {score.tfidf_similarity_score:.2f} / 25.0")
    print(f"Matched Required Skills: {', '.join(score.skill_breakdown.matched_required_skills)}")
    print(f"Missing Required Skills: {', '.join(score.skill_breakdown.missing_required_skills)}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Automated Resume Screening Tool — CLI & Server Entry Point"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run batch screening simulation on sample resumes"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Launch the FastAPI server"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to an individual resume file to screen"
    )
    parser.add_argument(
        "--job",
        type=str,
        default="JD-001",
        help="Target Job Description ID (default: JD-001)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the API server (default: 8000)"
    )

    args = parser.parse_args()

    if args.serve:
        start_server(port=args.port)
    elif args.file:
        sys.exit(analyze_single_file(args.file, job_id=args.job))
    else:
        # Default action: run the sample simulation
        sys.exit(run_sample_simulation(job_id=args.job))


if __name__ == "__main__":
    main()
