"""Unit tests for DocumentExtractor."""

import unittest
from pathlib import Path
from src.resume_screening.extraction.extractor import DocumentExtractor


class TestDocumentExtractor(unittest.TestCase):

    def test_clean_text_strips_emails_and_urls(self):
        sample = "Contact me at candidate@example.com or visit https://myportfolio.io for details."
        cleaned = DocumentExtractor.clean_text(sample)
        self.assertNotIn("candidate@example.com", cleaned)
        self.assertNotIn("https://myportfolio.io", cleaned)
        self.assertIn("Contact me at", cleaned)

    def test_extract_candidate_name_from_text(self):
        sample = "SARAH CONNOR\nSummary:\nExperienced Engineer..."
        name = DocumentExtractor.extract_candidate_name(sample)
        self.assertEqual(name, "Sarah Connor")

    def test_estimate_experience_years_explicit(self):
        sample = "Software Engineer with 6+ years of experience building APIs."
        years = DocumentExtractor.estimate_experience_years(sample)
        self.assertEqual(years, 6.0)

    def test_estimate_experience_years_unknown(self):
        """Focused test: resumes with no year counts or date ranges return None without crashing."""
        sample = "Junior developer with skills in Python and Git. Interested in learning new technologies."
        years = DocumentExtractor.estimate_experience_years(sample)
        self.assertIsNone(years)

    def test_estimate_experience_years_empty_text(self):
        """Verifies empty or whitespace text returns None cleanly."""
        self.assertIsNone(DocumentExtractor.estimate_experience_years(""))
        self.assertIsNone(DocumentExtractor.estimate_experience_years("   \n\t  "))

    def test_detect_sections(self):
        sample = "Professional Summary\nWork Experience\nEducation\nTechnical Skills\nProjects"
        sections = DocumentExtractor.detect_sections(sample)
        self.assertTrue(sections["summary"])
        self.assertTrue(sections["experience"])
        self.assertTrue(sections["education"])
        self.assertTrue(sections["skills"])
        self.assertTrue(sections["projects"])


if __name__ == "__main__":
    unittest.main()
