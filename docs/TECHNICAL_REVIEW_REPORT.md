# Technical Manager Audit Report: Project Readiness for GitHub

**Date:** November 20, 2026  
**Project:** Automated Resume Screening Tool  
**Auditor:** Antigravity AI Technical Review  
**Project Scope:** Educational / Student Portfolio Project (Prototype)  
**Target Repository:** Public / Private GitHub Publication  
**Verdict:** **READY FOR GITHUB AS A PORTFOLIO / STUDENT PROJECT (WITH PRE-FLIGHT ACTION ITEMS)**

---

## 1. Executive Summary

This audit assesses the code quality, repository structure, security, dependencies, testing, and GitHub readiness of the **Automated Resume Screening Tool** (`Automated-Resume-Screening-Tool`) and its companion **Beginner Version** (`beginner_version`).

### Project Maturity Classification
> **Note on Classification:** This project is classified as an **educational / student portfolio demonstration**, not an enterprise production-ready system. It demonstrates full-stack software development principles (FastAPI backend, Next.js frontend, document parsing, TF-IDF NLP matching, and modular testing), but intentionally lacks production-grade features such as persistent relational databases, user authentication/authorization, asynchronous background task queues (e.g., Celery/Redis), rate limiting, and production observability.

### Verification Environment Notice
- **Environment:** Windows 11 / PowerShell session with `BypassSandbox: true`.
- **Python Runtime:** `.\venv\Scripts\python.exe` (Python 3.13.14, Microsoft Store reparse point). In standard sandbox mode without bypass, Windows blocks access to this virtual environment binary with *"The file cannot be accessed by the system"*.
- **Git Status:** **UNVERIFIED / BLOCKED**. The `git` command is not available in the execution `PATH`. Working tree cleanliness could not be inspected via `git status` and must be verified by the user prior to committing.

---

## 2. Readiness Scorecard

| Assessment Domain | Status | Rating | Evaluation Details |
| :--- | :---: | :---: | :--- |
| **Directory & File Hierarchy** | Passed | 10/10 | Strictly matches the required project layout (`src/`, `frontend/`, `tests/`, `docs/`, `resumes/`, `data/`). |
| **Architecture (Portfolio Scope)** | Passed | 9.0/10 | Clean separation of extraction, skill matching, multi-factor scoring, and API routing. |
| **Test Verification (Independently Run)** | Passed | 10/10 | **20 of 20 tests passed** in 4.67s via pytest (exit code 0). |
| **Simulation Verification (Independently Run)**| Passed | 10/10 | `python main.py --simulate` completed successfully (exit code 0). |
| **Live Services (Independently Run)** | Passed | 10/10 | FastAPI (`http://127.0.0.1:8000/api/health`) and Next.js (`http://localhost:3000`) both returned HTTP 200. |
| **PII & Secrets Hygiene** | Passed | 10/10 | 100% synthetic resumes (`@example.test`, `@example.com`); no real candidate personal data or hardcoded credentials. |
| **Dependency Specification** | Corrected | 7.5/10 | Uses **minimum version constraints (`>=`)**, NOT pinned exact versions (`==`). |
| **Repository Hygiene (`.gitignore`)** | Review | 8.5/10 | Rules exist for `venv`, `.env`, `node_modules`, `.next`, but live git working tree is uninspected (`git` missing in PATH). |
| **Open Source Governance** | Advisory | 7.0/10 | Lacks a `LICENSE` file and an automated GitHub Actions CI workflow. |

---

## 3. Independent Execution & Verification Evidence

All checks below were **independently executed** using `.\venv\Scripts\python.exe` on Windows with `BypassSandbox: true`.

### 3.1 Automated Test Suite Run

**Command:**
```powershell
.\venv\Scripts\python.exe -m pytest -v tests/
```
**Exit Code:** `0`  
**Raw Test Results:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\agarw\OneDrive\Desktop\New folder\python\resume screening
plugins: anyio-4.16.0, cov-7.1.0
collected 20 items

tests/test_api.py::TestAPIEndpoints::test_batch_screening PASSED         [  5%]
tests/test_api.py::TestAPIEndpoints::test_get_jobs PASSED                [ 10%]
tests/test_api.py::TestAPIEndpoints::test_get_skills PASSED              [ 15%]
tests/test_api.py::TestAPIEndpoints::test_health_endpoint PASSED         [ 20%]
tests/test_api.py::TestAPIEndpoints::test_root_endpoint PASSED           [ 25%]
tests/test_api.py::TestAPIEndpoints::test_screen_upload_unsupported_format PASSED [ 30%]
tests/test_api.py::TestAPIEndpoints::test_screen_uploaded_resume PASSED  [ 35%]
tests/test_extractor.py::TestDocumentExtractor::test_clean_text_strips_emails_and_urls PASSED [ 40%]
tests/test_extractor.py::TestDocumentExtractor::test_detect_sections PASSED [ 45%]
tests/test_extractor.py::TestDocumentExtractor::test_estimate_experience_years_empty_text PASSED [ 50%]
tests/test_extractor.py::TestDocumentExtractor::test_estimate_experience_years_explicit PASSED [ 55%]
tests/test_extractor.py::TestDocumentExtractor::test_estimate_experience_years_unknown PASSED [ 60%]
tests/test_extractor.py::TestDocumentExtractor::test_extract_candidate_name_from_text PASSED [ 65%]
tests/test_matcher.py::TestSkillMatcher::test_alias_resolution PASSED    [ 70%]
tests/test_matcher.py::TestSkillMatcher::test_evaluate_skills_breakdown PASSED [ 75%]
tests/test_matcher.py::TestSkillMatcher::test_extract_canonical_skills PASSED [ 80%]
tests/test_scorer.py::TestResumeScorer::test_score_candidate_bounds PASSED [ 85%]
tests/test_scorer.py::TestResumeScorer::test_score_candidate_unknown_experience_does_not_crash PASSED [ 90%]
tests/test_scorer.py::TestResumeScorer::test_tfidf_cosine_similarity_disjoint_text PASSED [ 95%]
tests/test_scorer.py::TestResumeScorer::test_tfidf_cosine_similarity_identical_text PASSED [100%]

======================== 20 passed, 1 warning in 4.67s ========================
```
*(Warning: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`)*

---

### 3.2 CLI Batch Simulation Run

**Command:**
```powershell
.\venv\Scripts\python.exe main.py --simulate
```
**Exit Code:** `0`  
**Actual Simulation Decision Labels & Output:**
> **Correction Note:** In the main application simulation (`main.py`), candidate fit categories are labeled **`Strong Match`** and **`Weak Match`** (not `Shortlist`/`Review`, which is used in `beginner_version`).

```text
================================================================================
      AUTOMATED RESUME SCREENING TOOL — BATCH SIMULATION ENGINE
================================================================================

[+] TARGET JOB PROFILE: Senior AI / Machine Learning Engineer (JD-001)
    Required Experience : 5.0 years
    Required Skills     : Python, PyTorch, Machine Learning, Natural Language Processing, FastAPI, Docker
    Preferred Skills    : Transformers, LangChain, Kubernetes, AWS, PostgreSQL, MLOps

[+] INGESTING & PARSING RESUMES (5 detected)...
    - Parsed 'alex_rivera_fullstack_developer.txt' -> Alex Rivera (4.0 yrs exp, 23 skills detected)
    - Parsed 'elena_rostova_junior_python_developer.txt' -> Elena Rostova (7.0 yrs exp, 13 skills detected)
    - Parsed 'marcus_vance_cloud_devops_engineer.txt' -> Marcus Vance (5.0 yrs exp, 14 skills detected)
    - Parsed 'priya_sharma_data_scientist.txt' -> Priya Sharma (3.0 yrs exp, 20 skills detected)
    - Parsed 'sarah_chen_senior_ai_engineer.txt' -> Sarah Chen (6.0 yrs exp, 33 skills detected)

[+] SCORING & RANKING CANDIDATES...

================================================================================
RANK  | CANDIDATE NAME         | SCORE   | FIT CATEGORY   | REQ SKILLS   | EXP (YRS)
--------------------------------------------------------------------------------
1     | Sarah Chen             |  77.5% | Strong Match   | 6/6          | 6.0      
2     | Alex Rivera            |  39.9% | Weak Match     | 3/6          | 4.0      
3     | Marcus Vance           |  36.4% | Weak Match     | 2/6          | 5.0      
4     | Priya Sharma           |  33.5% | Weak Match     | 3/6          | 3.0      
5     | Elena Rostova          |  32.5% | Weak Match     | 2/6          | 7.0      
================================================================================

[✓] SIMULATION COMPLETE. Report saved to: outputs\sample_screening_report.json
```

---

### 3.3 Live Service Probing

**Command:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing
Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
```
**Results:**
- FastAPI Backend: `HTTP 200 OK` (JSON: `{"status": "healthy", "service": "Automated Resume Screening API", ...}`)
- Next.js Recruiter Dashboard: `HTTP 200 OK` (Compiled HTML document, 461 modules compiled in development mode)

---

## 4. Inconsistencies & Corrections Analysis

### 4.1 Dependency Pinning Claim: Corrected
- **Previous Claim:** "Pinned dependencies in `requirements.txt`."
- **Actual Code:** `requirements.txt` specifies lower bounds with `>=` (e.g., `fastapi>=0.111.0`, `scikit-learn>=1.4.0`, `pydantic>=2.7.0`), not exact pinned versions (`==`).
- **Correction:** Clarified as *minimum version constraints*. For strict reproducibility across machines, generating a `requirements-lock.txt` or `pip freeze > requirements.lock` is recommended for future production releases.

### 4.2 Simulation Fit Categories: Corrected
- **Previous Claim:** Simulation labeled Sarah Chen as "Shortlist" and Alex Rivera as "Review".
- **Actual Code:** `main.py` simulation maps scores to **`Strong Match`** (>= 70%) and **`Weak Match`** (< 70%). The `Shortlist`/`Review` thresholding logic belongs to the `beginner_version/screener.py` project.

### 4.3 Test Suite Names: Corrected
- **Previous Claim:** Reported hallucinated test function names (`test_score_calculation_weights`, `test_alias_resolution`, `test_calculate_similarity_orthogonal`, etc.).
- **Actual Code:** The test suite consists of 20 distinct tests across `TestAPIEndpoints`, `TestDocumentExtractor`, `TestSkillMatcher`, and `TestResumeScorer`. All exact 20 names are now recorded verbatim from the pytest output in Section 3.1.

### 4.4 Git Working Tree Status: Unverified
- **Previous Claim:** "Repository hygiene verified clean."
- **Actual Status:** When invoking `git status --short`, PowerShell returned:
  ```
  git : The term 'git' is not recognized as the name of a cmdlet, function, script file, or operable program.
  ```
  Because Git CLI is not installed or not in system PATH, working tree cleanliness **cannot be verified by automated tools in this environment**.

---

## 5. Security, Ethics & Privacy Review

1. **Candidate PII Audit:** Passed. Resumes in `resumes/sample/` use fictitious identities (Sarah Chen, Alex Rivera, Elena Rostova, Marcus Vance, Priya Sharma) and example domains (`@example.test`, `@example.com`).
2. **Secret Leakage:** Passed. No private keys, database connection strings, or cloud tokens are present. `.gitignore` explicitly filters `.env` files.
3. **Algorithmic Ethics:** Passed. Both documentation and user-facing CLI outputs note that keyword extraction and cosine similarity scores measure lexical overlap and must serve solely as recruiter decision-support aids, not automated hiring rejections.

---

## 6. Pre-Flight Checklist for GitHub Release

Before publishing to GitHub, the repository owner should perform the following actions:

- [ ] **Install Git / Use GitHub Desktop:** Since `git` is not in the system terminal PATH, use GitHub Desktop or install Git for Windows to stage and commit files.
- [ ] **Verify Working Tree Exclusions:** Ensure `venv/`, `.venv/`, `frontend/node_modules/`, `frontend/.next/`, and `.pytest_cache/` are untracked and not staged for commit.
- [ ] **Add a LICENSE File:** Create a root `LICENSE` file (e.g. MIT License) to clarify open-source terms.
- [ ] **Optional CI Workflow:** Add `.github/workflows/ci.yml` to run `pytest -v tests/` automatically on future GitHub Pull Requests.

---

## 7. Technical Manager Sign-Off

**Status:** **Approved for GitHub Publication as a Student / Portfolio Project.**  
The repository exhibits clean structure, sound object-oriented and functional separation, 100% test pass rate, and verified live API/dashboard endpoints.
