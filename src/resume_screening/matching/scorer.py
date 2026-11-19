"""Multi-factor candidate scoring and ranking engine."""

import math
import re
from collections import Counter
from typing import List, Dict, Optional, Tuple
from ..schemas import JobDescription, ExtractedResume, CandidateScore, SkillMatchBreakdown
from .matcher import SkillMatcher


class ResumeScorer:
    """Scores and ranks resumes against job descriptions using multi-factor evaluation."""

    # Configurable weighting scheme (total: 100 points)
    WEIGHT_REQUIRED_SKILLS = 40.0
    WEIGHT_PREFERRED_SKILLS = 20.0
    WEIGHT_TFIDF_SIMILARITY = 25.0
    WEIGHT_EXPERIENCE = 15.0

    def __init__(self, skill_matcher: Optional[SkillMatcher] = None):
        self.matcher = skill_matcher or SkillMatcher()

    def compute_tfidf_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """Computes TF-IDF Cosine Similarity with Scikit-learn or pure Python fallback."""
        if not text_a.strip() or not text_b.strip():
            return 0.0

        # Try scikit-learn first
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            matrix = vec.fit_transform([text_a, text_b])
            sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
            return max(0.0, min(1.0, sim))
        except (ImportError, Exception):
            pass

        # Robust pure-Python TF-IDF Cosine Similarity implementation
        def tokenize(text: str) -> List[str]:
            return re.findall(r"\b[a-zA-Z0-9\+\#]{2,}\b", text.lower())

        tokens_a = tokenize(text_a)
        tokens_b = tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0

        docs = [tokens_a, tokens_b]
        num_docs = 2

        # Document frequencies
        df: Dict[str, int] = Counter()
        for doc in docs:
            unique_terms = set(doc)
            for term in unique_terms:
                df[term] += 1

        # TF-IDF vectors
        vocab = list(df.keys())
        def tfidf_vector(tokens: List[str]) -> Dict[str, float]:
            tf = Counter(tokens)
            doc_len = len(tokens)
            vec: Dict[str, float] = {}
            for term in vocab:
                if term in tf:
                    term_tf = tf[term] / doc_len
                    term_idf = math.log((num_docs + 1) / (df[term] + 1)) + 1.0
                    vec[term] = term_tf * term_idf
                else:
                    vec[term] = 0.0
            return vec

        vec_a = tfidf_vector(tokens_a)
        vec_b = tfidf_vector(tokens_b)

        # Dot product & magnitudes
        dot_product = sum(vec_a[t] * vec_b[t] for t in vocab)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0

        sim = dot_product / (mag_a * mag_b)
        return max(0.0, min(1.0, float(sim)))

    def score_candidate(self, resume: ExtractedResume, job: JobDescription) -> CandidateScore:
        """Scores an individual candidate resume against a job description."""
        # 1. Skill extraction and breakdown
        skills = resume.extracted_skills
        if not skills:
            skills = self.matcher.extract_skills_from_text(resume.clean_text)

        breakdown = self.matcher.evaluate_skills(
            candidate_skills=skills,
            required_skills=job.required_skills,
            preferred_skills=job.preferred_skills
        )

        # 2. Factor: Required Skills (max 40)
        req_score = round(breakdown.required_skill_match_ratio * self.WEIGHT_REQUIRED_SKILLS, 2)

        # 3. Factor: Preferred Skills (max 20)
        pref_score = round(breakdown.preferred_skill_match_ratio * self.WEIGHT_PREFERRED_SKILLS, 2)

        # 4. Factor: TF-IDF Cosine Text Similarity (max 25)
        # Combine job title and description
        job_full_text = f"{job.title} {' '.join(job.required_skills)} {' '.join(job.preferred_skills)} {job.description}"
        sim_ratio = self.compute_tfidf_cosine_similarity(resume.clean_text, job_full_text)
        tfidf_score = round(sim_ratio * self.WEIGHT_TFIDF_SIMILARITY, 2)

        # 5. Factor: Experience Alignment (max 15)
        req_exp = job.experience_years_required
        cand_exp = resume.estimated_experience_years
        if req_exp <= 0:
            exp_ratio = 1.0
        elif cand_exp is None:
            # Handle resumes where experience is unknown without crashing
            exp_ratio = 0.0
        elif cand_exp >= req_exp:
            exp_ratio = 1.0
        else:
            exp_ratio = max(0.0, cand_exp / req_exp)
        exp_score = round(exp_ratio * self.WEIGHT_EXPERIENCE, 2)

        # Total Composite Score
        total = round(req_score + pref_score + tfidf_score + exp_score, 2)
        total = max(0.0, min(100.0, total))

        # Categorize Fit
        if total >= 75.0:
            fit_category = "Strong Match"
        elif total >= 50.0:
            fit_category = "Moderate Match"
        else:
            fit_category = "Weak Match"

        candidate_name = resume.candidate_name or resume.filename

        return CandidateScore(
            rank=0,  # assigned in batch ranking
            filename=resume.filename,
            candidate_name=candidate_name,
            total_score=total,
            fit_category=fit_category,
            required_skill_score=req_score,
            preferred_skill_score=pref_score,
            tfidf_similarity_score=tfidf_score,
            experience_score=exp_score,
            estimated_experience_years=cand_exp,
            skill_breakdown=breakdown,
            extracted_skills=skills
        )

    def rank_candidates(
        self,
        resumes: List[ExtractedResume],
        job: JobDescription
    ) -> List[CandidateScore]:
        """Scores and ranks a collection of resumes in descending order of fit."""
        scored_candidates = [self.score_candidate(r, job) for r in resumes]

        # Sort: total_score desc, then required_skill_score desc, then tfidf_similarity_score desc
        scored_candidates.sort(
            key=lambda c: (c.total_score, c.required_skill_score, c.tfidf_similarity_score),
            reverse=True
        )

        # Assign ordinal ranks (1-indexed)
        for idx, candidate in enumerate(scored_candidates, start=1):
            candidate.rank = idx

        return scored_candidates
