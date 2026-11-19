"""Skill extraction and matching against taxonomy and job requirements."""

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from ..schemas import SkillMatchBreakdown


class SkillMatcher:
    """Detects technical skills in text and maps against job requirements."""

    def __init__(self, skills_data_path: Optional[str] = None):
        self.skills_by_category: Dict[str, List[str]] = {}
        self.aliases: Dict[str, str] = {}
        self.canonical_skills: Set[str] = set()

        if skills_data_path is None:
            # Default to data/skills.json relative to repository root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            skills_data_path = str(base_dir / "data" / "skills.json")

        self._load_skills(skills_data_path)

    def _load_skills(self, file_path: str) -> None:
        """Loads skill taxonomy and alias mappings."""
        p = Path(file_path)
        if not p.exists():
            # Fallback basic skill taxonomy if file missing
            self.canonical_skills = {
                "Python", "TypeScript", "JavaScript", "SQL", "Docker", "Kubernetes",
                "FastAPI", "React", "Next.js", "PyTorch", "TensorFlow", "Scikit-learn",
                "Machine Learning", "Natural Language Processing", "PostgreSQL", "AWS"
            }
            return

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.skills_by_category = data.get("categories", {})
        self.aliases = {k.lower(): v for k, v in data.get("aliases", {}).items()}

        for cat, skills in self.skills_by_category.items():
            for s in skills:
                self.canonical_skills.add(s)

        # Also add alias targets
        for target in self.aliases.values():
            self.canonical_skills.add(target)

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Detects skills present in resume text."""
        if not text:
            return []

        lower_text = text.lower()
        detected_canonical: Set[str] = set()

        # Check canonical skills
        for skill in self.canonical_skills:
            # Escape skill for regex, handling +, #, etc.
            escaped = re.escape(skill.lower())
            # Use boundary regex that respects special characters like C++ or Next.js
            # Do not treat sentence-ending period as part of an attached word
            pattern = rf"(?<![\w\+#]){escaped}(?![\w\+#]|(\.(?=[a-z0-9])))"
            if re.search(pattern, lower_text):
                detected_canonical.add(skill)

        # Check aliases
        for alias, canonical_name in self.aliases.items():
            escaped = re.escape(alias)
            pattern = rf"(?<![\w\+#]){escaped}(?![\w\+#]|(\.(?=[a-z0-9])))"
            if re.search(pattern, lower_text):
                detected_canonical.add(canonical_name)

        return sorted(list(detected_canonical))

    def evaluate_skills(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> SkillMatchBreakdown:
        """Compares candidate skills against job required and preferred skills."""
        cand_set = {s.lower() for s in candidate_skills}

        # Resolve any required skills through aliases
        def match_skill(target_skill: str) -> bool:
            t_low = target_skill.lower()
            if t_low in cand_set:
                return True
            # Check if canonical name matches
            canonical = self.aliases.get(t_low, target_skill).lower()
            if canonical in cand_set:
                return True
            # Check if any candidate skill matches through aliases
            for c in cand_set:
                if self.aliases.get(c, c).lower() == t_low or self.aliases.get(c, c).lower() == canonical:
                    return True
            return False

        matched_req = [s for s in required_skills if match_skill(s)]
        missing_req = [s for s in required_skills if s not in matched_req]

        matched_pref = [s for s in preferred_skills if match_skill(s)]
        missing_pref = [s for s in preferred_skills if s not in matched_pref]

        req_ratio = len(matched_req) / len(required_skills) if required_skills else 1.0
        pref_ratio = len(matched_pref) / len(preferred_skills) if preferred_skills else 1.0

        return SkillMatchBreakdown(
            matched_required_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            missing_preferred_skills=missing_pref,
            required_skill_match_ratio=round(req_ratio, 3),
            preferred_skill_match_ratio=round(pref_ratio, 3)
        )
