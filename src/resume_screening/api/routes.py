"""API routes for resume extraction, skill matching, screening, and reporting.

Enforces documented file size limits, safe temporary file handling,
and clear separation between uploaded resume screening and bundled sample screening.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from ..schemas import (
    JobDescription,
    ExtractedResume,
    CandidateScore,
    BatchScreeningResponse,
    HealthResponse,
)
from ..extraction.extractor import DocumentExtractor
from ..matching.matcher import SkillMatcher
from ..matching.scorer import ResumeScorer

router = APIRouter(prefix="/api", tags=["Resume Screening"])

# Configuration constants
MAX_UPLOAD_SIZE_MB = 5
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Resolve directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RESUMES_DIR = BASE_DIR / "resumes" / "sample"
OUTPUTS_DIR = BASE_DIR / "outputs"

matcher = SkillMatcher(str(DATA_DIR / "skills.json"))
scorer = ResumeScorer(matcher)


def load_job_fixtures() -> List[JobDescription]:
    """Loads default job descriptions from data/job_descriptions.json."""
    job_file = DATA_DIR / "job_descriptions.json"
    if not job_file.exists():
        return []
    with open(job_file, "r", encoding="utf-8") as f:
        raw_list = json.load(f)
    return [JobDescription(**j) for j in raw_list]


def resolve_target_job(job_id: Optional[str], custom_job_json: Optional[str]) -> JobDescription:
    """Resolves target job description from preset fixture ID or custom JSON."""
    if custom_job_json:
        try:
            job_dict = json.loads(custom_job_json)
            return JobDescription(**job_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid custom job specification: {e}"
            )

    jobs = load_job_fixtures()
    for j in jobs:
        if j.id.lower() == (job_id or "").lower():
            return j

    if jobs:
        return jobs[0]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Job description '{job_id}' not found."
    )


async def read_and_validate_upload(file: UploadFile) -> bytes:
    """Validates file extension and enforces documented maximum file size."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in DocumentExtractor.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Must be one of: {sorted(list(DocumentExtractor.SUPPORTED_EXTENSIONS))}"
        )

    # Read up to MAX_UPLOAD_SIZE_BYTES + 1 to detect size violations without unbounded memory allocation
    chunk = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(chunk) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB."
        )

    return chunk


def parse_upload_safely(content: bytes, original_filename: str) -> ExtractedResume:
    """Writes bytes to a safely generated temporary file, parses content, and guarantees cleanup."""
    ext = Path(original_filename or "resume.txt").suffix.lower()
    temp_path: Optional[Path] = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=tempfile.gettempdir(),
            prefix="resume_upload_",
            suffix=ext,
            delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        raw_text = DocumentExtractor.extract_text(str(temp_path))
    finally:
        # Guarantee removal on both success and failure
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    clean_text = DocumentExtractor.clean_text(raw_text)
    candidate_name = DocumentExtractor.extract_candidate_name(raw_text, original_filename)
    exp_years = DocumentExtractor.estimate_experience_years(raw_text)
    sections = DocumentExtractor.detect_sections(raw_text)
    skills = matcher.extract_skills_from_text(clean_text)

    return ExtractedResume(
        filename=original_filename or "uploaded_resume",
        candidate_name=candidate_name,
        raw_text=raw_text,
        clean_text=clean_text,
        extracted_skills=skills,
        estimated_experience_years=exp_years,
        sections_detected=sections
    )


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint providing system status, fixture counts, and upload limits."""
    jobs = load_job_fixtures()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        available_jobs_count=len(jobs),
        skill_vocabulary_size=len(matcher.canonical_skills),
        max_upload_size_mb=MAX_UPLOAD_SIZE_MB
    )


@router.get("/jobs", response_model=List[JobDescription])
def get_jobs():
    """List all available benchmark job descriptions."""
    return load_job_fixtures()


@router.get("/jobs/{job_id}", response_model=JobDescription)
def get_job_by_id(job_id: str):
    """Retrieve details for a specific job description."""
    jobs = load_job_fixtures()
    for j in jobs:
        if j.id.lower() == job_id.lower():
            return j
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job description with ID '{job_id}' not found.")


@router.get("/skills")
def get_skills_vocabulary():
    """Retrieve categorized skill taxonomy and aliases."""
    skills_file = DATA_DIR / "skills.json"
    if not skills_file.exists():
        return {"categories": {}, "aliases": {}}
    with open(skills_file, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/extract", response_model=ExtractedResume)
async def extract_resume(
    file: UploadFile = File(..., description="Uploaded resume file (.txt, .pdf, .docx, max 5MB)")
):
    """Uploads a single resume, enforces max file size (5MB), and returns parsed structured data."""
    content = await read_and_validate_upload(file)
    return parse_upload_safely(content, file.filename or "uploaded_resume")


@router.post("/screen", response_model=CandidateScore)
async def screen_uploaded_resume(
    file: UploadFile = File(..., description="Uploaded resume file to screen (.txt, .pdf, .docx, max 5MB)"),
    job_id: str = Form("JD-001", description="Target benchmark job description ID"),
    custom_job_json: Optional[str] = Form(None, description="Optional custom job description JSON string")
):
    """Screens an individually uploaded resume file against a specified job description.
    
    Enforces maximum file size (5MB), safely parses the document, computes multi-factor scores
    (TF-IDF cosine similarity, required/preferred skills, experience fit), and returns candidate scorecard.
    """
    content = await read_and_validate_upload(file)
    extracted = parse_upload_safely(content, file.filename or "uploaded_resume")
    target_job = resolve_target_job(job_id, custom_job_json)

    score = scorer.score_candidate(extracted, target_job)
    score.rank = 1
    return score


@router.post("/screen/batch", response_model=BatchScreeningResponse)
def screen_bundled_sample_resumes(
    job_id: Optional[str] = "JD-001",
    custom_job_json: Optional[str] = None
):
    """Screens all bundled synthetic sample resumes in resumes/sample/ against a job description.
    
    Iterates through all sample resumes, scores them against the target job profile,
    and returns ranked candidate scorecards ordered by descending composite score.
    """
    target_job = resolve_target_job(job_id, custom_job_json)

    # Ingest all bundled synthetic sample resumes
    parsed_resumes: List[ExtractedResume] = []
    if RESUMES_DIR.exists():
        for file_path in sorted(RESUMES_DIR.iterdir()):
            if file_path.suffix.lower() in DocumentExtractor.SUPPORTED_EXTENSIONS:
                raw_text = DocumentExtractor.extract_text(str(file_path))
                clean_text = DocumentExtractor.clean_text(raw_text)
                candidate_name = DocumentExtractor.extract_candidate_name(raw_text, file_path.name)
                exp_years = DocumentExtractor.estimate_experience_years(raw_text)
                sections = DocumentExtractor.detect_sections(raw_text)
                skills = matcher.extract_skills_from_text(clean_text)

                parsed_resumes.append(ExtractedResume(
                    filename=file_path.name,
                    candidate_name=candidate_name,
                    raw_text=raw_text,
                    clean_text=clean_text,
                    extracted_skills=skills,
                    estimated_experience_years=exp_years,
                    sections_detected=sections
                ))

    # Rank candidates
    ranked = scorer.rank_candidates(parsed_resumes, target_job)
    strong_count = sum(1 for c in ranked if c.fit_category == "Strong Match")

    return BatchScreeningResponse(
        job_id=target_job.id,
        job_title=target_job.title,
        total_candidates_screened=len(ranked),
        strong_matches_count=strong_count,
        ranked_candidates=ranked,
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@router.post("/reports/generate")
def generate_report(job_id: str = "JD-001"):
    """Runs batch screening on bundled sample resumes and saves a report to outputs/."""
    batch_result = screen_bundled_sample_resumes(job_id=job_id)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUTS_DIR / f"screening_report_{job_id.lower()}.json"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(batch_result.model_dump_json(indent=2))

    return {
        "status": "success",
        "message": f"Report successfully generated and saved to {report_file.name}",
        "file_path": str(report_file),
        "total_screened": batch_result.total_candidates_screened,
        "top_candidate": batch_result.ranked_candidates[0].candidate_name if batch_result.ranked_candidates else None
    }
