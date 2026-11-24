"""Document text extractor for TXT, PDF, and DOCX files.

Includes zero-external-dependency fallbacks for PDF and DOCX formats.
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Dict, Any, Optional


class DocumentExtractor:
    """Extracts, cleans, and structures raw text from resume documents."""

    SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".doc"}

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from supported document types."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found at path: {file_path}")

        ext = path.suffix.lower()
        if ext == ".txt":
            return cls._extract_txt(path)
        elif ext == ".pdf":
            return cls._extract_pdf(path)
        elif ext in (".docx", ".doc"):
            return cls._extract_docx(path)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: {cls.SUPPORTED_EXTENSIONS}")

    @staticmethod
    def _extract_txt(path: Path) -> str:
        """Extract plain text with encoding fallback."""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Fallback binary decode ignoring errors
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")

    @classmethod
    def _extract_pdf(cls, path: Path) -> str:
        """Extract text from PDF using pypdf, pdfplumber, or pure-python fallback."""
        # Try pypdf first if available
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except (ImportError, Exception):
            pass

        # Try pdfplumber if available
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                text = "\n".join(pages).strip()
                if text:
                    return text
        except (ImportError, Exception):
            pass

        # Pure-Python heuristic text stream decoder for PDF
        try:
            with open(path, "rb") as f:
                content = f.read().decode("latin-1", errors="ignore")
            # Extract strings between BT (Begin Text) and ET (End Text) or Tj/TJ tokens
            text_chunks = []
            for stream in re.findall(r"BT(.*?)ET", content, re.DOTALL):
                strings = re.findall(r"\((.*?)\)[\s]*Tj", stream)
                if strings:
                    text_chunks.extend(strings)
            if text_chunks:
                return "\n".join(text_chunks)
        except Exception:
            pass

        return ""

    @staticmethod
    def _extract_docx(path: Path) -> str:
        """Extract text from DOCX using python-docx or zero-dependency XML parsing."""
        # Try python-docx if installed
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except (ImportError, Exception):
            pass

        # Zero-dependency DOCX extraction via internal word/document.xml
        try:
            with zipfile.ZipFile(str(path)) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # Find all w:t (text) nodes in WordprocessingML namespace
            texts = []
            for elem in tree.iter():
                if elem.tag.endswith("}t") and elem.text:
                    texts.append(elem.text)
            return " ".join(texts)
        except Exception as e:
            return f"[Error extracting DOCX: {e}]"

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Sanitizes text: removes URLs, emails, phone numbers, and abnormal whitespaces."""
        if not raw_text:
            return ""

        text = raw_text
        # Strip URLs
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        # Strip emails
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " ", text)
        # Strip phone numbers (e.g. +1-555-0192)
        text = re.sub(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", " ", text)
        # Strip non-standard punctuation / non-ASCII noise while retaining coding punctuation (+, #)
        text = re.sub(r"[^\w\s\+\#\.\-]", " ", text)
        # Compress multiple spaces / tabs / newlines
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def extract_candidate_name(raw_text: str, filename: str = "") -> str:
        """Infers candidate name from top lines of resume or filename."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for line in lines[:5]:
            # Look for lines that look like a person's name (2-4 words, capitalized, no keywords)
            words = line.split()
            if 2 <= len(words) <= 4:
                disqualifiers = {"resume", "curriculum", "vitae", "summary", "profile", "contact", "email", "phone"}
                if not any(d in line.lower() for d in disqualifiers):
                    if all(w.replace("-", "").replace(".", "").isalpha() for w in words):
                        return line.title()

        # Fallback to parsing filename
        if filename:
            clean_name = Path(filename).stem
            clean_name = re.sub(r"[_.-]+", " ", clean_name)
            # Remove role identifiers if any
            clean_name = re.sub(r"\b(senior|junior|lead|developer|engineer|scientist|ai|ml|fullstack|resume|cv)\b", "", clean_name, flags=re.IGNORECASE)
            clean_name = " ".join(clean_name.split()).title()
            if clean_name:
                return clean_name

        return "Candidate"

    # Backward-compatible alias
    extract_candidate_name_from_text = extract_candidate_name

    @staticmethod
    def estimate_experience_years(raw_text: str) -> Optional[float]:
        """Extracts estimated years of professional experience using regex heuristics.
        
        Returns None if experience is unknown or cannot be reliably determined.
        """
        if not raw_text or not raw_text.strip():
            return None

        # Pattern 1: Explicit years statement, e.g., '6+ years of experience', '4 years'
        exp_pattern = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s+(?:of\s+)?(?:experience|exp)?", raw_text, re.IGNORECASE)
        if exp_pattern:
            years = [float(y) for y in exp_pattern if 0.0 < float(y) <= 40]
            if years:
                return max(years)

        # Pattern 2: Year intervals, e.g. '2019 - 2024' or '2019 - Present'
        year_ranges = re.findall(r"\b(20\d{2}|19\d{2})\s*(?:-|to)\s*(20\d{2}|present|current)\b", raw_text, re.IGNORECASE)
        current_year = 2026
        accumulated_years = 0.0
        for start_str, end_str in year_ranges:
            try:
                start = int(start_str)
                end = current_year if end_str.lower() in ("present", "current") else int(end_str)
                diff = end - start
                if 0 < diff <= 30:
                    accumulated_years += diff
            except ValueError:
                continue

        if accumulated_years > 0.0:
            return min(round(accumulated_years, 1), 30.0)

        return None

    @staticmethod
    def detect_sections(raw_text: str) -> Dict[str, bool]:
        """Detect standard resume sections."""
        lower = raw_text.lower()
        return {
            "summary": any(k in lower for k in ("summary", "profile", "objective")),
            "experience": any(k in lower for k in ("experience", "work history", "employment")),
            "education": any(k in lower for k in ("education", "degree", "university", "academic")),
            "skills": any(k in lower for k in ("skills", "technical skills", "technologies", "competencies")),
            "projects": any(k in lower for k in ("projects", "open source", "portfolio")),
            "certifications": any(k in lower for k in ("certifications", "licenses", "courses"))
        }
