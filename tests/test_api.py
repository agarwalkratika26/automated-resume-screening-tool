"""Unit tests for FastAPI routes and endpoints."""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from src.resume_screening.api.app import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "operational")

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertGreaterEqual(data.get("available_jobs_count", 0), 1)
        self.assertGreaterEqual(data.get("skill_vocabulary_size", 0), 1)
        self.assertEqual(data.get("max_upload_size_mb"), 5)

    def test_get_jobs(self):
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)
        jobs = response.json()
        self.assertIsInstance(jobs, list)
        self.assertGreaterEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "JD-001")

    def test_get_skills(self):
        response = self.client.get("/api/skills")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("categories", data)
        self.assertIn("aliases", data)

    def test_batch_screening(self):
        response = self.client.post("/api/screen/batch?job_id=JD-001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("job_id"), "JD-001")
        self.assertGreaterEqual(data.get("total_candidates_screened", 0), 1)
        self.assertIn("ranked_candidates", data)

    def test_screen_uploaded_resume(self):
        sample_file = PROJECT_ROOT / "resumes" / "sample" / "sarah_chen_senior_ai_engineer.txt"
        self.assertTrue(sample_file.exists(), f"Sample resume not found: {sample_file}")

        with open(sample_file, "rb") as f:
            response = self.client.post(
                "/api/screen",
                files={"file": ("sarah_chen.txt", f, "text/plain")},
                data={"job_id": "JD-001"}
            )
        self.assertEqual(response.status_code, 200)
        candidate = response.json()
        self.assertIn("Sarah Chen", candidate.get("candidate_name", ""))
        self.assertGreaterEqual(candidate.get("total_score", 0), 50.0)

    def test_screen_upload_unsupported_format(self):
        response = self.client.post(
            "/api/screen",
            files={"file": ("malicious.exe", b"binarycontent", "application/octet-stream")},
            data={"job_id": "JD-001"}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
