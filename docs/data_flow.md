# Data Flow & Pipeline Lifecycle

## 1. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / CLI User
    participant UI as Next.js Dashboard / CLI
    participant API as FastAPI Router (/api/screen/batch)
    participant Extractor as DocumentExtractor
    participant Matcher as SkillMatcher
    participant Scorer as ResumeScorer
    participant Store as Outputs Directory

    Recruiter->>UI: Select Job Profile (e.g. JD-001) & Initiate Screening
    UI->>API: POST /api/screen/batch?job_id=JD-001
    
    rect rgb(240, 248, 255)
    Note over API,Extractor: Extraction Stage
    API->>Extractor: Ingest resume files from resumes/sample/
    Extractor->>Extractor: Extract text (PDF / DOCX / TXT)
    Extractor->>Extractor: Clean text & detect sections
    Extractor->>Extractor: Estimate years of experience
    Extractor-->>API: ExtractedResume objects
    end

    rect rgb(245, 245, 255)
    Note over API,Matcher: Skill Mapping Stage
    API->>Matcher: Extract skills from clean text
    Matcher->>Matcher: Apply alias dictionary (e.g. k8s -> Kubernetes)
    Matcher-->>API: Detected canonical skills
    end

    rect rgb(255, 245, 245)
    Note over API,Scorer: Scoring & Ranking Stage
    API->>Scorer: rank_candidates(resumes, target_job)
    Scorer->>Scorer: Compute Required Skills Score (40 pts max)
    Scorer->>Scorer: Compute Preferred Skills Score (20 pts max)
    Scorer->>Scorer: Compute TF-IDF Cosine Similarity (25 pts max)
    Scorer->>Scorer: Compute Experience Score (15 pts max)
    Scorer->>Scorer: Sum Composite Total (0-100 pts)
    Scorer->>Scorer: Assign Ranks (1 to N) & Fit Categories
    Scorer-->>API: Ranked CandidateScore list
    end

    API->>Store: Persist screening_report.json (optional)
    API-->>UI: BatchScreeningResponse JSON payload
    UI-->>Recruiter: Display Interactive Candidate Scorecards
```

---

## 2. Stage-by-Stage Data Transformations

| Stage | Input Data | Transformation Applied | Output Data |
| :--- | :--- | :--- | :--- |
| **1. Ingestion** | Raw `.txt`, `.pdf`, `.docx` files | File byte streaming and format decoding | Raw text string `raw_text` |
| **2. Sanitization** | `raw_text` | Regex removal of emails, phone numbers, URLs, and excessive whitespace | Sanitized text `clean_text` |
| **3. Section Parsing** | `raw_text` | Keyword heuristic detection (Experience, Education, Skills, Projects) | `sections_detected: Dict[str, bool]` |
| **4. Experience Inference** | `raw_text` | Pattern matching date ranges (`2019 - Present`) and explicit year statements | `estimated_experience_years: Optional[float]` (`None` if unknown) |
| **5. Skill Extraction** | `clean_text` | Word-boundary regex matching against `skills.json` taxonomy and aliases | `extracted_skills: List[str]` |
| **6. Skill Comparison** | `extracted_skills`, `job.required_skills` | Set-intersection with alias normalization | `SkillMatchBreakdown` (matched vs. missing) |
| **7. TF-IDF Similarity** | `clean_text`, `job.description` | Vector space cosine similarity | TF-IDF text similarity ratio $\in [0.0, 1.0]$ |
| **8. Composite Scoring** | Score components | Multi-factor weighted summation | Composite score $\in [0.0, 100.0]$ |
| **9. Ranking & Output** | Unordered candidates | Descending sort by composite score, tie-break by required skills | Ordered list with ranks and fit badges |
