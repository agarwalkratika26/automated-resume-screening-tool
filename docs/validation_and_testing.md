# Verification, Testing & Quality Assurance Guide

This guide establishes the protocols, commands, and expected criteria for verifying the correctness of every subsystem within the **Automated Resume Screening Tool**.

---

## 1. Validation Matrix

| Component | Target Verification | Command / Method | Expected Result |
| :--- | :--- | :--- | :--- |
| **Document Extraction** | TXT / PDF / DOCX parsing, text sanitization, experience heuristics | `pytest tests/test_extractor.py` | Valid strings returned; emails/URLs stripped; correct section and year detection. |
| **Skill Matching** | Skill taxonomy lookup and alias resolution | `pytest tests/test_matcher.py` | Aliases like `k8s` and `nlp` resolve to canonical forms; boundary matching prevents false positives. |
| **Scoring Engine** | Multi-factor weighting and TF-IDF similarity | `pytest tests/test_scorer.py` | Scores sum to $\le 100$; ranking sorts descending; ties broken correctly. |
| **CLI Simulation** | End-to-end batch screening | `python main.py --simulate` | Reads all 5 synthetic resumes, outputs formatted terminal table, creates `outputs/sample_screening_report.json`. |
| **FastAPI Backend** | Health check & REST routes | `python -m pytest tests/test_api.py` or curl `http://localhost:8000/api/health` | Returns status 200, valid JSON schemas matching Pydantic contracts. |
| **Next.js Dashboard** | Frontend compilation & rendering | `cd frontend && npm run build` | Zero build errors; valid TypeScript compilation; production bundles generated. |

---

## 2. Automated Test Commands

### Running Python Unit Tests
```bash
# Run all unit tests with verbose reporting
pytest -v tests/

# Run with test coverage
pytest --cov=src tests/
```

### Running the End-to-End Simulation
```bash
python main.py --simulate
```
*Expected Output:* An ASCII scorecard ranking Sarah Chen (#1), Alex Rivera (#2), Priya Sharma (#3), Marcus Vance (#4), and Elena Rostova (#5) against `JD-001`.

### Validating the Frontend
```bash
cd frontend
npm install
npm run lint
npm run build
```

---

## 3. Environment Sanity Check (Zero External Dependencies)
If running in an environment without pip-installed packages, all core algorithms (TF-IDF vectorizer, cosine similarity, regex matcher, text extraction) are designed to run cleanly using standard Python library primitives (`math`, `re`, `collections`, `json`, `pathlib`, `zipfile`, `xml.etree`).
