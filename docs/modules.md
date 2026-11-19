# Module & Component Breakdown

This document provides a comprehensive technical reference for every module and file across the refactored project structure.

---

## 1. Directory Tree & Module Mapping

```
Automated-Resume-Screening-Tool/
│
├── resumes/
│   └── sample/                    # Synthetic candidate resumes (zero PII)
│       ├── sarah_chen_senior_ai_engineer.txt
│       ├── alex_rivera_fullstack_developer.txt
│       ├── priya_sharma_data_scientist.txt
│       ├── marcus_vance_cloud_devops_engineer.txt
│       └── elena_rostova_junior_python_developer.txt
│
├── data/                          # Benchmark fixtures
│   ├── job_descriptions.json      # Structured job specifications
│   └── skills.json                # Categorized skill taxonomy and alias dictionary
│
├── src/
│   └── resume_screening/         # Core application package
│       ├── __init__.py            # Package metadata
│       ├── schemas.py             # Pydantic data transfer objects
│       │
│       ├── extraction/            # Document parsing subsystem
│       │   ├── __init__.py
│       │   └── extractor.py       # DocumentExtractor class (TXT, PDF, DOCX)
│       │
│       ├── matching/              # Intelligence and evaluation engine
│       │   ├── __init__.py
│       │   ├── matcher.py         # SkillMatcher (taxonomy & alias resolution)
│       │   └── scorer.py          # ResumeScorer (multi-factor scoring & ranking)
│       │
│       └── api/                   # FastAPI service layer
│           ├── __init__.py
│           ├── routes.py          # REST endpoints
│           └── app.py             # FastAPI app factory & CORS configuration
│
├── frontend/                      # Next.js 14 Recruiter Dashboard
│   ├── app/
│   │   ├── layout.tsx             # Root dashboard layout
│   │   ├── page.tsx               # Interactive recruiter scoreboard
│   │   └── globals.css            # TailwindCSS styling
│   ├── package.json               # Frontend dependencies & scripts
│   ├── tsconfig.json              # TypeScript compiler configuration
│   ├── next.config.js             # API proxy rewrites & standalone output
│   └── tailwind.config.js         # Design token configuration
│
├── outputs/                       # Generated candidate reports
│   ├── .gitkeep                   # Directory placeholder
│   └── sample_screening_report.json # Pre-generated batch simulation report
│
├── images/                        # Visual assets and diagrams
│   └── architecture.svg           # System architecture diagram
│
├── docs/                          # Comprehensive technical documentation
│   ├── README.md
│   ├── architecture.md
│   ├── data_flow.md
│   ├── modules.md
│   ├── dataset.md
│   ├── model_training.md
│   ├── api_reference.md
│   ├── validation_and_testing.md
│   └── implementation_log.md
│
├── README.md                      # GitHub-ready root repository overview
├── requirements.txt               # Backend Python dependencies
├── .gitignore                     # Git ignore rules
└── main.py                        # Unified Python CLI & server entry point
```

---

## 2. Python Backend Module Details

### `src.resume_screening.schemas`
Defines strict Pydantic v2 data models:
- `JobDescription`: Schema for job requirements, required/preferred skills, and experience criteria.
- `ExtractedResume`: Data container for raw text, clean text, detected skills, and estimated experience.
- `SkillMatchBreakdown`: Matched and missing required/preferred skills and match ratios.
- `CandidateScore`: Final multi-factor evaluation containing total score, fit category, breakdown scores, and rank.
- `BatchScreeningResponse`: Response payload encapsulating ranked candidate scorecards.
- `HealthResponse`: System status and loaded fixture counts.

### `src.resume_screening.extraction.extractor.DocumentExtractor`
- `extract_text(file_path: str) -> str`: Routes file path by extension (`.txt`, `.pdf`, `.docx`).
- `clean_text(raw_text: str) -> str`: Normalizes whitespace, removes URLs, emails, phone numbers, and noise while preserving programming symbols.
- `extract_candidate_name(raw_text: str, filename: str) -> str`: Heuristic inference of candidate name from resume headers or filename.
- `estimate_experience_years(raw_text: str) -> Optional[float]`: Extracts professional experience using regex interval detection; returns `None` if experience is unknown.
- `detect_sections(raw_text: str) -> Dict[str, bool]`: Flags standard sections (Summary, Experience, Education, Skills, Projects).

### `src.resume_screening.matching.matcher.SkillMatcher`
- `_load_skills(file_path: str)`: Ingests `skills.json` and builds canonical skill sets and lowercase alias maps.
- `extract_skills_from_text(text: str) -> List[str]`: Scans text using word-boundary regular expressions and normalizes aliases.
- `evaluate_skills(candidate_skills, required_skills, preferred_skills) -> SkillMatchBreakdown`: Calculates matched vs. missing skills and match ratios.

### `src.resume_screening.matching.scorer.ResumeScorer`
- `compute_tfidf_cosine_similarity(text_a: str, text_b: str) -> float`: Computes cosine similarity between document vectors using `scikit-learn` or a pure-Python TF-IDF vectorizer fallback.
- `score_candidate(resume: ExtractedResume, job: JobDescription) -> CandidateScore`: Evaluates an individual candidate across 4 weighted factors:
  - Required Skills (40 pts)
  - Preferred Skills (20 pts)
  - TF-IDF Cosine Similarity (25 pts)
  - Experience Alignment (15 pts; gracefully handles `None` as 0 pts)
- `rank_candidates(resumes: List[ExtractedResume], job: JobDescription) -> List[CandidateScore]`: Scores, sorts descending, and assigns ranks (1, 2, ...).

### `src.resume_screening.api`
- `app.py`: Sets up FastAPI application, enables CORS for `http://localhost:3000`, and attaches API routers.
- `routes.py`: Implements `/api/health`, `/api/jobs`, `/api/extract` (upload & parse with 5MB ceiling), `/api/screen` (upload & screen single resume with 5MB ceiling), `/api/screen/batch` (batch screening on bundled sample resumes), and `/api/reports/generate`.
