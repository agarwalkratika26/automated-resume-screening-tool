# Implementation Log & Audit Trail

This document logs all refactoring operations, architectural migrations, file additions, and validation results.

---

## Engineering Audit Entries

### [Phase 1] — Project Refactoring to Target GitHub-Ready Structure
- **Date:** 2026-11-19
- **Goal:** Transform repository into the target `Automated-Resume-Screening-Tool` standard structure while preserving and expanding FastAPI backend, Next.js dashboard, synthetic data, scoring engine, and documentation.
- **Actions Completed:**
  1. **Folder Hierarchy Created:**
     - `resumes/sample/`: Synthetic resumes directory.
     - `data/`: Job descriptions and skill taxonomy fixtures.
     - `src/resume_screening/`: Core Python package (`api/`, `extraction/`, `matching/`, `schemas.py`).
     - `frontend/`: Next.js 14 recruiter dashboard.
     - `outputs/`: Output directory for generated screening reports.
     - `images/`: SVG architectural diagram.
     - `docs/`: Technical documentation hub.
  2. **Data & Synthetic Fixtures:**
     - Created 5 realistic synthetic resumes in `resumes/sample/` (Senior AI Engineer, Full Stack Developer, Data Scientist, Cloud DevOps Engineer, Junior Python Developer) with strictly zero personal identifiable information.
     - Created `data/job_descriptions.json` with 3 benchmark job profiles (`JD-001`, `JD-002`, `JD-003`).
     - Created `data/skills.json` with 7 skill domains, 50+ canonical skills, and an extensive alias dictionary.
  3. **Backend & Algorithms:**
     - Implemented `DocumentExtractor` with multi-format support (`.txt`, `.pdf`, `.docx`) and zero-dependency fallbacks.
     - Implemented `SkillMatcher` with alias normalization and boundary-safe regex.
     - Implemented `ResumeScorer` with multi-factor weighting (40% required, 20% preferred, 25% TF-IDF cosine similarity, 15% experience). Built resilient pure-Python TF-IDF cosine similarity fallback.
     - Implemented FastAPI application and REST endpoints (`/api/health`, `/api/jobs`, `/api/extract`, `/api/screen/batch`, `/api/reports/generate`).
  4. **Frontend Recruiter Dashboard:**
     - Next.js 14 App Router dashboard in `frontend/` featuring interactive job profile selection, candidate scorecards, skill gap badges, and an offline fallback simulation engine.
  5. **CLI & Server (`main.py`):**
     - Single entry point with `--simulate`, `--serve`, and `--file` commands.
  6. **Configuration & Governance:**
     - Added comprehensive root `requirements.txt` and `.gitignore`.
     - Built `outputs/sample_screening_report.json` and `images/architecture.svg`.
- **Validation Performed:**
  - Verified directory structure and file locations.
  - Confirmed documentation references and internal links.

### [Phase 2] — Review Findings & Hardening Pass
- **Date:** 2026-11-19
- **Review Items Addressed:**
  1. **Upload Safety & File Size Ceiling:** Enforced 5MB (`MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024`) limit on `/api/extract` and `/api/screen` returning `HTTP 413`. Replaced direct filename path construction with `tempfile.NamedTemporaryFile` in system temp directory and guaranteed cleanup via `try ... finally`.
  2. **Unknown Experience Resilience:** Updated `estimate_experience_years` to return `None` when experience is unstated or undetectable. Updated `CandidateScore` and `ExtractedResume` schemas (`Optional[float] = None`). Hardened `scorer.py` and `main.py` formatting so resumes with unknown experience calculate safely without throwing `TypeError`. Authored focused unit tests in `tests/test_extractor.py` and `tests/test_scorer.py`.
  3. **Similarity Label Realignment:** Replaced all inaccurate "semantic similarity" labels with "TF-IDF cosine similarity" or "text similarity" across `schemas.py`, `scorer.py`, `frontend/app/page.tsx`, `README.md`, `images/architecture.svg`, and documentation.
  4. **API Behavior & Routing Consistency:** Added dedicated `POST /api/screen` endpoint for evaluating individually uploaded resume files against jobs, and clarified that `POST /api/screen/batch` screens bundled sample resumes in `resumes/sample/`. Documented in `README.md` and `docs/api_reference.md`.
  5. **Runtime Validation Clarification:** Confirmed and documented runtime verification blockers in current Windows environment (Windows execution alias stub for Python; Node.js not registered in PATH).

### [Phase 3] — Recruiter Dashboard Upload Integration & CORS Hardening
- **Date:** 2026-11-19
- **Implemented:**
  1. **Dashboard Upload Picker:** Integrated an interactive resume file picker into [`frontend/app/page.tsx`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/frontend/app/page.tsx) with client-side format checks (`.txt`, `.pdf`, `.docx`), 5MB size guardrails, and connection to `POST /api/screen`.
  2. **Error & Feedback Handling:** Added visible alert banners for unsupported extensions, payload size limits (HTTP 413), and backend connectivity failures. Successfully screened resumes are added directly into the candidate comparison leaderboard.
  3. **Sample Batch Demo Separation:** Retained bundled sample batch evaluations via a distinct "⚡ Run Bundled Batch Demo" action.
  4. **Strict CORS Policy:** Updated [`src/resume_screening/api/app.py`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/src/resume_screening/api/app.py) to specify explicit local development origins (`http://localhost:3000`, `http://127.0.0.1:3000`, etc.) and eliminated wildcard origin usage with credentials.
- **Verification Performed:**
  - Validated frontend TypeScript/JSX structure and API contracts.
  - Re-verified JSON schema parsing across all project fixtures.
  - Attempted runtime verification of Python, pytest, and Node.js.

### [Phase 4] — Consistency Audit: Upload Flow, Origin Parity & cURL Specifications
- **Date:** 2026-11-19
- **Implemented:**
  1. **Development Origins Parity:** Aligned `README.md` and `docs/api_reference.md` with [`src/resume_screening/api/app.py`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/src/resume_screening/api/app.py), explicitly enumerating all 4 supported local development origins (`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`, `http://127.0.0.1:3001`).
  2. **cURL & Workflow Consistency:** Added end-to-end cURL upload examples for `/api/screen` and `/api/extract` to both `README.md` and `docs/api_reference.md`, detailing file parameters and multipart form-data usage.
  3. **Verification of Backend vs. Frontend Contracts:** Audited parameters between `page.tsx` (`file`, `job_id`), `routes.py` (`File(...)`, `Form(...)`), and error response handling (HTTP 413, HTTP 400).
- **Verification Performed:**
  - Ran static JSON validation suite across all project fixtures.
  - Executed runtime checks for Python and Node.js.

### [Phase 5] — Staged File Selection & Submission Consistency
- **Date:** 2026-11-19
- **Implemented:**
  1. **UI Staging Separation:** Updated [`frontend/app/page.tsx`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/frontend/app/page.tsx) so file selection stages the document (`stagedFile`) and displays a staged file badge with file size and a clear button.
  2. **Explicit Submission Trigger:** Clicking "Upload & Screen" now submits the staged file to `POST /api/screen` with `isUploading` feedback. If no file is staged, the button is disabled.
  3. **Documentation Alignment:** Synchronized [`README.md`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/README.md) to explicitly describe this two-step staging and submission workflow.
- **Verification Performed:**
  - Validated JSON fixtures and static project files.
  - Executed runtime checks for Python and Node.js.

### [Review Sign-Off] — Staging Flow & Documentation Parity Confirmed
- **Date:** 2026-11-19
- **Status:** Complete.
- **Review Findings:** Confirmed parity between [`frontend/app/page.tsx`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/frontend/app/page.tsx) and [`README.md`](file:///c:/Users/agarw/OneDrive/Desktop/New folder/python/resume screening/README.md). Selecting a file validates and stages it without triggering a network request; the "Upload & Screen" button explicitly submits to `POST /api/screen`; and the "Clear" action unstages the file. No further code modifications required for this workflow.
- **Runtime Verification Status:** Retained strictly as **BLOCKED** as Python 3.10+, pytest, and Node.js/npm runtimes remain uninstalled/unregistered in the system environment.
