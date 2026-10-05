import unittest
import os
import sys

# Ensure app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.azure_analyzer import AzureResumeAnalyzer

class TestAzureAnalyzerScoring(unittest.TestCase):
    def setUp(self):
        self.analyzer = AzureResumeAnalyzer()

    def test_skills_overlap_and_missing_skills(self):
        resume_text = """
        Jane Doe - Python Developer
        Skills: Python, FastAPI, Docker, PostgreSQL, Git
        Experience: Built web applications using FastAPI and deployed on Docker.
        """
        job_text = "Looking for a Python developer with experience in FastAPI, Docker, and Kubernetes."
        
        resume_entities = {
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "Git"],
            "job_titles": ["Python Developer"],
            "organizations": [],
            "education": [],
            "key_phrases": ["web applications"]
        }
        job_entities = {
            "skills": ["Python", "FastAPI", "Docker", "Kubernetes"],
            "job_titles": ["Python Developer"],
            "organizations": [],
            "education": [],
            "key_phrases": ["python developer"]
        }

        score, breakdown, matched, missing = self.analyzer.calculate_match_score(
            resume_text=resume_text,
            resume_entities=resume_entities,
            job_text=job_text,
            job_entities=job_entities
        )

        matched_lower = [m.lower() for m in matched]
        missing_lower = [m.lower() for m in missing]

        # Python, FastAPI, Docker should match; Kubernetes should be missing
        self.assertTrue("python" in matched_lower)
        self.assertTrue("fastapi" in matched_lower)
        self.assertTrue("docker" in matched_lower)
        self.assertTrue("kubernetes" in missing_lower)
        
        # Check score bounds and breakdown
        self.assertTrue(0 <= score <= 100)
        self.assertEqual(breakdown["skills_score"], 75.0)  # 3 out of 4 skills matched = 75%
        self.assertTrue(0 <= breakdown["keywords_score"] <= 100)
        self.assertTrue(0 <= breakdown["experience_score"] <= 100)
        self.assertTrue(0 <= breakdown["education_score"] <= 100)

    def test_perfect_match_score(self):
        text = "Python FastAPI Docker AWS PostgreSQL"
        entities = {
            "skills": ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL"],
            "job_titles": ["Backend Engineer"],
            "organizations": ["TechCorp"],
            "education": ["Computer Science Bachelor"],
            "key_phrases": ["backend engineer", "cloud infrastructure"]
        }

        score, breakdown, matched, missing = self.analyzer.calculate_match_score(
            resume_text=text,
            resume_entities=entities,
            job_text=text,
            job_entities=entities
        )

        self.assertGreaterEqual(score, 80)
        self.assertEqual(breakdown["skills_score"], 100.0)
        self.assertEqual(len(missing), 0)
        self.assertEqual(len(matched), 5)

    def test_zero_match_score(self):
        resume_text = "Experienced Chef with Culinary Arts background in French cuisine and pastry preparation."
        job_text = "Senior DevOps Cloud Engineer skilled in Kubernetes, Terraform, AWS, and Golang."

        resume_entities = {
            "skills": ["Culinary Arts", "Baking"],
            "job_titles": ["Chef"],
            "organizations": [],
            "education": [],
            "key_phrases": ["french cuisine"]
        }
        job_entities = {
            "skills": ["Kubernetes", "Terraform", "AWS", "Golang"],
            "job_titles": ["DevOps Cloud Engineer"],
            "organizations": [],
            "education": [],
            "key_phrases": ["cloud infrastructure"]
        }

        score, breakdown, matched, missing = self.analyzer.calculate_match_score(
            resume_text=resume_text,
            resume_entities=resume_entities,
            job_text=job_text,
            job_entities=job_entities
        )

        self.assertEqual(breakdown["skills_score"], 0.0)
        self.assertEqual(len(matched), 0)
        self.assertEqual(len(missing), 4)
        self.assertLess(score, 55)

    def test_resume_quality_checks(self):
        complete_resume = """
        Alex Smith | alex.smith@example.com | (555) 123-4567 | linkedin.com/in/alexsmith | github.com/alexsmith
        
        PROFESSIONAL SUMMARY
        Results-driven Software Engineer with 4 years of experience delivering scalable web systems.
        
        TECHNICAL SKILLS
        Python, FastAPI, Docker, SQL, Git, Linux
        
        WORK EXPERIENCE
        Software Engineer at Acme Corp (2022 - Present)
        - Architected and implemented microservices using FastAPI and Docker.
        - Optimized database queries, reducing response latency by 35%.
        - Spearheaded migration of legacy services to cloud infrastructure.
        
        PROJECTS
        Intelligent Resume Builder: Developed automated resume analyzer with ATS scoring.
        
        EDUCATION
        Bachelor of Science in Computer Science - State University
        """
        
        entities = {
            "skills": ["Python", "FastAPI", "Docker", "SQL", "Git", "Linux"],
            "job_titles": ["Software Engineer"],
            "organizations": ["Acme Corp"],
            "education": ["Bachelor of Science in Computer Science"],
            "key_phrases": ["scalable web systems"]
        }

        report = self.analyzer.check_resume_quality(
            resume_text=complete_resume,
            resume_entities=entities,
            missing_skills=[]
        )

        # All key sections should be detected
        self.assertTrue(report["sections_detected"]["summary"])
        self.assertTrue(report["sections_detected"]["skills"])
        self.assertTrue(report["sections_detected"]["experience"])
        self.assertTrue(report["sections_detected"]["education"])
        self.assertTrue(report["sections_detected"]["projects"])

        # Contact info checks
        self.assertTrue(report["contact_info"]["email"])
        self.assertTrue(report["contact_info"]["phone"])
        self.assertTrue(report["contact_info"]["linkedin"])
        self.assertTrue(report["contact_info"]["github"])

        # Action verbs should be identified
        self.assertGreaterEqual(len(report["action_verbs_found"]), 3)
        self.assertTrue(any(verb in report["action_verbs_found"] for verb in ["architected", "implemented", "optimized", "spearheaded", "developed"]))
        self.assertIn(report["overall_quality"], ["Excellent", "Good"])

    def test_app_resume_to_text(self):
        resume_data = {
            "personal_info": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": "+1-800-555-0199",
                "professional_title": "Full Stack Developer",
                "location": "New York, NY",
                "linkedin": "https://linkedin.com/in/johndoe",
                "portfolio": "https://johndoe.dev"
            },
            "summary": "Full Stack developer passionate about clean code and modern web frameworks.",
            "skills": ["Python", "React", "Docker", "PostgreSQL"],
            "projects": [
                {
                    "name": "E-Commerce Platform",
                    "description": "Built using React and FastAPI.",
                    "technologies": ["React", "FastAPI", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "institution": "Tech Institute",
                    "degree": "B.Tech",
                    "field": "Computer Science",
                    "graduation_year": 2024
                }
            ]
        }

        formatted_text = self.analyzer.app_resume_to_text(resume_data)

        self.assertIn("John Doe", formatted_text)
        self.assertIn("john@example.com", formatted_text)
        self.assertIn("Full Stack Developer", formatted_text)
        self.assertIn("Python, React, Docker, PostgreSQL", formatted_text)
        self.assertIn("E-Commerce Platform", formatted_text)
        self.assertIn("Tech Institute", formatted_text)

if __name__ == "__main__":
    unittest.main()
