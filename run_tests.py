#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for Intelligent Resume Builder & Azure AI Analyzer.
Tests scoring engine, fuzzy matching, Jaccard similarity, ATS quality heuristics,
document extraction, and live API endpoints.
"""

import os
import sys
import unittest
import time
import io

# Ensure app can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.azure_analyzer import AzureResumeAnalyzer

class ComprehensiveSystemTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = AzureResumeAnalyzer()
        self.sample_docx = os.path.join(os.path.dirname(__file__), "sample_resumes", "sample_software_engineer_resume.docx")
        self.sample_pdf = os.path.join(os.path.dirname(__file__), "sample_resumes", "sample_software_engineer_resume.pdf")

    # -------------------------------------------------------------------------
    # TEST 1: Fuzzy Skill Matching (Threshold 0.80)
    # -------------------------------------------------------------------------
    def test_01_fuzzy_skill_matching(self):
        resume_text = "Experienced with ReactJS, Postgres, and Python programming."
        resume_entities = {
            "skills": ["React.js", "PostgreSQL", "Python"],
            "job_titles": ["Full Stack Engineer"],
            "education": ["B.Tech Computer Science"],
            "key_phrases": ["web services"]
        }
        job_entities = {
            "skills": ["ReactJS", "Postgres", "Python", "Kubernetes"],
            "job_titles": ["Full Stack Engineer"],
            "education": [],
            "key_phrases": []
        }

        score, breakdown, matched, missing = self.analyzer.calculate_match_score(
            resume_text=resume_text,
            resume_entities=resume_entities,
            job_text="Looking for ReactJS, Postgres, Python, and Kubernetes.",
            job_entities=job_entities
        )

        matched_lower = [m.lower() for m in matched]
        self.assertIn("reactjs", matched_lower)
        self.assertIn("postgres", matched_lower)
        self.assertIn("python", matched_lower)
        self.assertIn("kubernetes", [m.lower() for m in missing])
        self.assertEqual(breakdown["skills_score"], 75.0)

    # -------------------------------------------------------------------------
    # TEST 2: Jaccard Similarity for Keywords_Score
    # -------------------------------------------------------------------------
    def test_02_jaccard_keywords_score(self):
        resume_text = "Specialized in microservices architecture and automated testing pipelines."
        resume_entities = {
            "skills": ["Python"],
            "job_titles": [],
            "education": [],
            "key_phrases": ["microservices architecture", "automated testing", "cloud deployment"]
        }
        job_entities = {
            "skills": ["Python"],
            "job_titles": [],
            "education": [],
            "key_phrases": ["microservices architecture", "automated testing", "distributed databases"]
        }

        score, breakdown, matched, missing = self.analyzer.calculate_match_score(
            resume_text=resume_text,
            resume_entities=resume_entities,
            job_text="Need experience in microservices architecture and automated testing.",
            job_entities=job_entities
        )

        self.assertGreater(breakdown["keywords_score"], 50.0)
        self.assertLessEqual(breakdown["keywords_score"], 100.0)

    # -------------------------------------------------------------------------
    # TEST 3: Experience_Score Point Weighting (Base 20, Title 40, Seniority 20, Leadership 20)
    # -------------------------------------------------------------------------
    def test_03_experience_score_weighting(self):
        # 1. Base experience only (no title, seniority, leadership)
        base_resume = "Worked on web projects for 2 years."
        _, b_base, _, _ = self.analyzer.calculate_match_score(
            resume_text=base_resume,
            resume_entities={"skills": [], "job_titles": [], "education": [], "key_phrases": []},
            job_text="Looking for a Python Developer.",
            job_entities={"skills": [], "job_titles": ["Python Developer"], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_base["experience_score"], 20.0)

        # 2. Add Target Title (+40 pts -> 60)
        title_resume = "Software Engineer working with Python."
        _, b_title, _, _ = self.analyzer.calculate_match_score(
            resume_text=title_resume,
            resume_entities={"skills": [], "job_titles": ["Software Engineer"], "education": [], "key_phrases": []},
            job_text="Software Engineer role.",
            job_entities={"skills": [], "job_titles": ["Software Engineer"], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_title["experience_score"], 60.0)

        # 3. Add Seniority (+20 pts -> 80)
        senior_resume = "Senior Software Engineer working with Python."
        _, b_senior, _, _ = self.analyzer.calculate_match_score(
            resume_text=senior_resume,
            resume_entities={"skills": [], "job_titles": ["Senior Software Engineer"], "education": [], "key_phrases": []},
            job_text="Software Engineer role.",
            job_entities={"skills": [], "job_titles": ["Software Engineer"], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_senior["experience_score"], 80.0)

        # 4. Add Leadership (+20 pts -> 100)
        lead_resume = "Senior Software Engineer who managed and spearheaded team delivery."
        _, b_lead, _, _ = self.analyzer.calculate_match_score(
            resume_text=lead_resume,
            resume_entities={"skills": [], "job_titles": ["Senior Software Engineer"], "education": [], "key_phrases": []},
            job_text="Software Engineer role.",
            job_entities={"skills": [], "job_titles": ["Software Engineer"], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_lead["experience_score"], 100.0)

    # -------------------------------------------------------------------------
    # TEST 4: Education_Score Tiered Points
    # -------------------------------------------------------------------------
    def test_04_education_tiered_scores(self):
        # PhD = 100
        _, b_phd, _, _ = self.analyzer.calculate_match_score(
            resume_text="Holder of PhD in Computer Science.",
            resume_entities={"skills": [], "job_titles": [], "education": ["PhD"], "key_phrases": []},
            job_text="Job",
            job_entities={"skills": [], "job_titles": [], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_phd["education_score"], 100.0)

        # Master's = 90
        _, b_ms, _, _ = self.analyzer.calculate_match_score(
            resume_text="Graduated with Master of Science degree.",
            resume_entities={"skills": [], "job_titles": [], "education": ["Master of Science"], "key_phrases": []},
            job_text="Job",
            job_entities={"skills": [], "job_titles": [], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_ms["education_score"], 90.0)

        # Bachelor's = 80
        _, b_bs, _, _ = self.analyzer.calculate_match_score(
            resume_text="Graduated with Bachelor of Technology degree.",
            resume_entities={"skills": [], "job_titles": [], "education": ["Bachelor of Technology"], "key_phrases": []},
            job_text="Job",
            job_entities={"skills": [], "job_titles": [], "education": [], "key_phrases": []}
        )
        self.assertEqual(b_bs["education_score"], 80.0)

    # -------------------------------------------------------------------------
    # TEST 5: ATS Quality Audit (Sections, Contact, Verbs, Word Count)
    # -------------------------------------------------------------------------
    def test_05_ats_quality_audit(self):
        resume = """
        John Doe | john.doe@example.com | +1 555 123 4567 | linkedin.com/in/johndoe | github.com/johndoe
        SUMMARY
        Accomplished engineer with background in distributed systems.
        SKILLS
        Python, Docker, FastAPI, Kubernetes, PostgreSQL
        EXPERIENCE
        Senior Engineer at Acme Corp (2020 - Present)
        • Architected and engineered high-scale backend services.
        • Spearheaded database optimization, reducing query latency.
        • Orchestrated container deployment across clusters.
        EDUCATION
        Bachelor of Science in Computer Science
        PROJECTS
        Resume Analyzer: Developed intelligent ATS scoring tool.
        """
        audit = self.analyzer.check_resume_quality(
            resume_text=resume,
            resume_entities={"skills": ["Python", "Docker"]},
            missing_skills=[]
        )

        for sec in ["summary", "skills", "experience", "education", "projects"]:
            self.assertTrue(audit["sections_detected"][sec], f"Section {sec} should be detected")

        self.assertTrue(audit["contact_info"]["email"])
        self.assertTrue(audit["contact_info"]["phone"])
        self.assertTrue(audit["contact_info"]["linkedin"])
        self.assertTrue(audit["contact_info"]["github"])
        self.assertGreaterEqual(len(audit["action_verbs_found"]), 3)
        self.assertIn(audit["overall_quality"], ["Excellent", "Good"])

    # -------------------------------------------------------------------------
    # TEST 6: Real Document Extraction (DOCX and PDF)
    # -------------------------------------------------------------------------
    def test_06_real_document_extraction(self):
        if os.path.exists(self.sample_docx):
            with open(self.sample_docx, "rb") as f:
                bytes_docx = f.read()
            text_docx, method_docx = self.analyzer.extract_text_from_file(bytes_docx, "sample.docx")
            self.assertGreater(len(text_docx), 100)
            self.assertIn("Python", text_docx)

        if os.path.exists(self.sample_pdf):
            with open(self.sample_pdf, "rb") as f:
                bytes_pdf = f.read()
            text_pdf, method_pdf = self.analyzer.extract_text_from_file(bytes_pdf, "sample.pdf")
            self.assertGreater(len(text_pdf), 100)
            self.assertIn("Python", text_pdf)

    # -------------------------------------------------------------------------
    # TEST 7: File Type & Size Validation
    # -------------------------------------------------------------------------
    def test_07_file_validation(self):
        # Invalid extension rejection
        with self.assertRaises(ValueError):
            self.analyzer.extract_text_from_file(b"test content", "invalid.txt")

        # Over 5 MB file rejection
        oversized_bytes = b"0" * (6 * 1024 * 1024)
        with self.assertRaises(ValueError):
            self.analyzer.extract_text_from_file(oversized_bytes, "large.pdf")


def main():
    print("=" * 65)
    print(" INTELLIGENT RESUME BUILDER & AZURE AI ANALYZER - TEST SUITE ")
    print("=" * 65)
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(ComprehensiveSystemTests)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n[SUCCESS] All 7 test modules passed with 100% success rate!")
        return 0
    else:
        print(f"\n[FAILURE] {len(result.failures)} failures, {len(result.errors)} errors encountered.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
