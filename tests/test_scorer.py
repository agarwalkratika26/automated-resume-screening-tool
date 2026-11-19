"""Unit tests for ResumeScorer."""

import unittest
from src.resume_screening.schemas import JobDescription, ExtractedResume
from src.resume_screening.matching.scorer import ResumeScorer


class TestResumeScorer(unittest.TestCase):

    def setUp(self):
        self.scorer = ResumeScorer()
        self.job = JobDescription(
            id="JD-TEST",
            title="AI Engineer",
            experience_years_required=5.0,
            required_skills=["Python", "PyTorch", "FastAPI"],
            preferred_skills=["Docker", "AWS"],
            description="Seeking an AI engineer skilled in Python and PyTorch."
        )

    def test_tfidf_cosine_similarity_identical_text(self):
        text = "python pytorch machine learning models"
        sim = self.scorer.compute_tfidf_cosine_similarity(text, text)
        self.assertAlmostEqual(sim, 1.0, places=2)

    def test_tfidf_cosine_similarity_disjoint_text(self):
        text_a = "gardening flowers horticulture"
        text_b = "kubernetes docker terraform aws"
        sim = self.scorer.compute_tfidf_cosine_similarity(text_a, text_b)
        self.assertEqual(sim, 0.0)

    def test_score_candidate_bounds(self):
        resume = ExtractedResume(
            filename="test_resume.txt",
            candidate_name="Jane Doe",
            raw_text="Jane Doe\nPython and PyTorch Engineer with 5 years experience.",
            clean_text="Jane Doe Python and PyTorch Engineer with 5 years experience.",
            extracted_skills=["Python", "PyTorch", "FastAPI", "Docker", "AWS"],
            estimated_experience_years=5.0
        )
        score = self.scorer.score_candidate(resume, self.job)
        self.assertGreaterEqual(score.total_score, 0.0)
        self.assertLessEqual(score.total_score, 100.0)
        self.assertEqual(score.fit_category, "Strong Match")
        self.assertEqual(score.required_skill_score, 40.0)
        self.assertEqual(score.preferred_skill_score, 20.0)
        self.assertGreaterEqual(score.tfidf_similarity_score, 0.0)
        self.assertEqual(score.experience_score, 15.0)

    def test_score_candidate_unknown_experience_does_not_crash(self):
        """Focused test: resume with estimated_experience_years=None calculates safely without crashing."""
        resume = ExtractedResume(
            filename="unknown_exp_resume.txt",
            candidate_name="Alex Student",
            raw_text="Recent graduate skilled in Python and FastAPI.",
            clean_text="Recent graduate skilled in Python and FastAPI.",
            extracted_skills=["Python", "FastAPI"],
            estimated_experience_years=None
        )
        score = self.scorer.score_candidate(resume, self.job)
        self.assertIsNone(score.estimated_experience_years)
        self.assertEqual(score.experience_score, 0.0)
        self.assertGreater(score.total_score, 0.0)
        self.assertIn(score.fit_category, ["Strong Match", "Moderate Match", "Weak Match"])


if __name__ == "__main__":
    unittest.main()
