"""Unit tests for SkillMatcher."""

import unittest
from src.resume_screening.matching.matcher import SkillMatcher


class TestSkillMatcher(unittest.TestCase):

    def setUp(self):
        self.matcher = SkillMatcher()

    def test_extract_canonical_skills(self):
        text = "Proficient in Python, SQL, Docker, and PyTorch for machine learning applications."
        skills = self.matcher.extract_skills_from_text(text)
        self.assertIn("Python", skills)
        self.assertIn("SQL", skills)
        self.assertIn("Docker", skills)
        self.assertIn("PyTorch", skills)
        self.assertIn("Machine Learning", skills)

    def test_alias_resolution(self):
        text = "Experience with k8s deployment and nlp models using sklearn."
        skills = self.matcher.extract_skills_from_text(text)
        self.assertIn("Kubernetes", skills)
        self.assertIn("Natural Language Processing", skills)
        self.assertIn("Scikit-learn", skills)

    def test_evaluate_skills_breakdown(self):
        candidate_skills = ["Python", "FastAPI", "Docker", "PostgreSQL"]
        required = ["Python", "FastAPI", "PyTorch"]
        preferred = ["Docker", "Kubernetes"]

        breakdown = self.matcher.evaluate_skills(candidate_skills, required, preferred)
        self.assertIn("Python", breakdown.matched_required_skills)
        self.assertIn("FastAPI", breakdown.matched_required_skills)
        self.assertIn("PyTorch", breakdown.missing_required_skills)
        self.assertIn("Docker", breakdown.matched_preferred_skills)
        self.assertIn("Kubernetes", breakdown.missing_preferred_skills)
        self.assertAlmostEqual(breakdown.required_skill_match_ratio, 2 / 3, places=2)


if __name__ == "__main__":
    unittest.main()
