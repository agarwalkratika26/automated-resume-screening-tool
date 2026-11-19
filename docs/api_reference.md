# FastAPI REST API Reference

The backend exposes RESTful endpoints for resume text extraction, job description management, single uploaded resume screening, batch candidate screening on bundled sample fixtures, and report export.

**Base URL:** `http://localhost:8000/api`  
**Interactive Swagger UI:** `http://localhost:8000/docs`  
**ReDoc Specification:** `http://localhost:8000/redoc`

---

## 🔒 Upload Security & Resource Constraints
- **Documented Maximum File Size:** 5 MB (`5 * 1024 * 1024` bytes). Requests exceeding this limit return `HTTP 413 Request Entity Too Large` before disk persistence.
- **Temporary File Isolation:** Uploads are written to randomly generated, prefix-isolated temporary files via `tempfile.NamedTemporaryFile` in the system temporary directory (eliminating path traversal vulnerabilities).
- **Guaranteed Cleanup:** Temporary files are unlinked in strict `try ... finally` blocks on both successful extraction and parsing failures.
- **CORS Policy:** Explicitly allows local development dashboard origins (`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`, `http://127.0.0.1:3001`) with `allow_credentials=True`. Disallows wildcard origins (`*`) with credentials to ensure cross-origin browser compatibility.

---

## Endpoints Inventory

### 1. Health & Configuration Check
- **Route:** `GET /api/health`
- **Description:** Checks server status and returns loaded job and vocabulary metrics along with upload constraints.
- **Example cURL Request:**
  ```bash
  curl -X GET "http://localhost:8000/api/health"
  ```
- **Response `200 OK`:**
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "available_jobs_count": 3,
    "skill_vocabulary_size": 58,
    "max_upload_size_mb": 5
  }
  ```

---

### 2. Upload & Screen Single Resume
- **Route:** `POST /api/screen`
- **Description:** Uploads an individual candidate resume file and immediately evaluates it against a specified target job profile.
- **Content-Type:** `multipart/form-data`
- **Form Parameters:**
  - `file`: Resume file (`.txt`, `.pdf`, `.docx`, strictly $\le$ 5MB).
  - `job_id`: Target benchmark job description ID (e.g. `JD-001`, default).
  - `custom_job_json` *(optional)*: Custom JobDescription JSON payload.
- **Example cURL Request:**
  ```bash
  curl -X POST "http://localhost:8000/api/screen" \
    -F "file=@resumes/sample/sarah_chen_senior_ai_engineer.txt" \
    -F "job_id=JD-001"
  ```
- **Response `200 OK`:**
  ```json
  {
    "rank": 1,
    "filename": "candidate_resume.pdf",
    "candidate_name": "Sarah Chen",
    "total_score": 93.8,
    "fit_category": "Strong Match",
    "required_skill_score": 40.0,
    "preferred_skill_score": 16.7,
    "tfidf_similarity_score": 22.1,
    "experience_score": 15.0,
    "estimated_experience_years": 6.0,
    "skill_breakdown": {
      "matched_required_skills": ["Python", "PyTorch", "Machine Learning", "Natural Language Processing", "FastAPI", "Docker"],
      "missing_required_skills": [],
      "matched_preferred_skills": ["Transformers", "LangChain", "Kubernetes", "AWS", "PostgreSQL"],
      "missing_preferred_skills": ["MLOps"],
      "required_skill_match_ratio": 1.0,
      "preferred_skill_match_ratio": 0.833
    },
    "extracted_skills": ["Python", "PyTorch", "FastAPI", "Docker", "AWS", "Transformers"]
  }
  ```

---

### 3. Upload & Extract Resume Only (No Scoring)
- **Route:** `POST /api/extract`
- **Description:** Ingests an uploaded resume file and returns parsed structured data (candidate name, clean text, detected skills, detected sections, and estimated experience).
- **Content-Type:** `multipart/form-data`
- **Body:** `file: UploadFile` (supported: `.txt`, `.pdf`, `.docx`, strictly $\le$ 5MB)
- **Example cURL Request:**
  ```bash
  curl -X POST "http://localhost:8000/api/extract" \
    -F "file=@resumes/sample/sarah_chen_senior_ai_engineer.txt"
  ```
- **Response `200 OK`:** `ExtractedResume` object.
- **Error `413 Request Entity Too Large`:** Returned if file size exceeds 5MB.
- **Error `400 Bad Request`:** Returned if file format is unsupported.

---

### 4. Screen Bundled Sample Resumes
- **Route:** `POST /api/screen/batch?job_id={job_id}`
- **Description:** Evaluates all bundled synthetic sample resumes in `resumes/sample/` against the specified job description, returning a ranked candidate leaderboard.
- **Query / Form Parameters:**
  - `job_id` *(optional, default "JD-001")*: Target benchmark job profile.
  - `custom_job_json` *(optional)*: Custom job description JSON string.
- **Example cURL Request:**
  ```bash
  curl -X POST "http://localhost:8000/api/screen/batch?job_id=JD-001"
  ```
- **Response `200 OK`:** `BatchScreeningResponse` object with `ranked_candidates`.

---

### 5. Generate & Save Bundled Screening Report
- **Route:** `POST /api/reports/generate?job_id={job_id}`
- **Description:** Runs batch screening on bundled sample resumes and saves a formatted JSON report to `outputs/screening_report_{job_id}.json`.
- **Example cURL Request:**
  ```bash
  curl -X POST "http://localhost:8000/api/reports/generate?job_id=JD-001"
  ```
- **Response `200 OK`:**
  ```json
  {
    "status": "success",
    "message": "Report successfully generated and saved to screening_report_jd-001.json",
    "file_path": ".../outputs/screening_report_jd-001.json",
    "total_screened": 5,
    "top_candidate": "Sarah Chen"
  }
  ```

---

### 6. Job Descriptions & Skill Vocabulary Endpoints
- **`GET /api/jobs`**: Returns all benchmark job description fixtures (`JD-001`, `JD-002`, `JD-003`).
- **`GET /api/jobs/{job_id}`**: Retrieves a specific job specification by ID.
- **`GET /api/skills`**: Retrieves the full categorized skill taxonomy and alias dictionary.
