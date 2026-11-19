"""Pydantic schemas and data transfer objects for Resume Screening."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Schema representing a job specification fixture or user input."""
    id: str = Field(..., description="Unique job identifier, e.g. JD-001")
    title: str = Field(..., description="Job role title")
    department: Optional[str] = Field("Engineering", description="Department or business unit")
    experience_years_required: float = Field(0.0, description="Minimum years of professional experience")
    required_skills: List[str] = Field(default_factory=list, description="Mandatory required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have or preferred skills")
    education_level: Optional[str] = Field(None, description="Expected educational qualifications")
    description: str = Field(..., description="Full text description of the job")


class ExtractedResume(BaseModel):
    """Parsed and normalized resume content."""
    filename: str = Field(..., description="Source file name")
    candidate_name: Optional[str] = Field(None, description="Inferred candidate name")
    raw_text: str = Field(..., description="Full extracted raw text")
    clean_text: str = Field(..., description="Sanitized and normalized text")
    extracted_skills: List[str] = Field(default_factory=list, description="All skills detected in resume")
    estimated_experience_years: Optional[float] = Field(
        None, description="Heuristic estimate of years of professional experience, or None if unknown"
    )
    sections_detected: Dict[str, bool] = Field(default_factory=dict, description="Identified resume sections")


class SkillMatchBreakdown(BaseModel):
    """Breakdown of skill matching against a Job Description."""
    matched_required_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    matched_preferred_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    required_skill_match_ratio: float = Field(0.0, ge=0.0, le=1.0)
    preferred_skill_match_ratio: float = Field(0.0, ge=0.0, le=1.0)


class CandidateScore(BaseModel):
    """Multi-factor screening score and ranking for a candidate."""
    rank: int = Field(..., description="Ranking position (1 is top match)")
    filename: str = Field(..., description="Resume filename")
    candidate_name: str = Field(..., description="Candidate name")
    total_score: float = Field(..., ge=0.0, le=100.0, description="Weighted composite score out of 100")
    fit_category: str = Field(..., description="'Strong Match', 'Moderate Match', or 'Weak Match'")

    # Detailed score components
    required_skill_score: float = Field(..., description="Weighted required skill score (out of 40)")
    preferred_skill_score: float = Field(..., description="Weighted preferred skill score (out of 20)")
    tfidf_similarity_score: float = Field(..., description="TF-IDF cosine text similarity score (out of 25)")
    experience_score: float = Field(..., description="Experience alignment score (out of 15)")

    # Detailed analytics
    estimated_experience_years: Optional[float] = Field(
        None, description="Estimated years of professional experience, or None if unknown"
    )
    skill_breakdown: SkillMatchBreakdown
    extracted_skills: List[str] = Field(default_factory=list)

    @property
    def semantic_similarity_score(self) -> float:
        """Backward compatibility alias for tfidf_similarity_score."""
        return self.tfidf_similarity_score


class ScreeningRequest(BaseModel):
    """Request payload for screening against a job description."""
    job_description_id: Optional[str] = None
    custom_job_description: Optional[JobDescription] = None


class BatchScreeningResponse(BaseModel):
    """Response containing ranked candidates for a specified job."""
    job_id: str
    job_title: str
    total_candidates_screened: int
    strong_matches_count: int
    ranked_candidates: List[CandidateScore]
    generated_at: str


class HealthResponse(BaseModel):
    """API health status schema."""
    status: str = "ok"
    version: str = "1.0.0"
    available_jobs_count: int
    skill_vocabulary_size: int
    max_upload_size_mb: int = Field(5, description="Maximum permitted upload size in megabytes")
