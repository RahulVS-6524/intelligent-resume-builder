# app/job_matcher.py
from typing import List, Dict
import random  # In real app, you'd connect to a job API

class JobMatcher:
    def __init__(self):
        # Sample job database (in real app, this would be from an API)
        self.sample_jobs = [
            {
                "title": "Senior Python Developer",
                "company": "TechCorp",
                "location": "Remote",
                "salary": "$120k - $150k",
                "required_skills": ["Python", "FastAPI", "Docker", "AWS"],
                "preferred_skills": ["Kubernetes", "React", "MongoDB"],
                "description": "Looking for experienced Python developer..."
            },
            {
                "title": "Full Stack Engineer",
                "company": "StartupXYZ",
                "location": "San Francisco",
                "salary": "$130k - $160k",
                "required_skills": ["JavaScript", "React", "Node.js", "Python"],
                "preferred_skills": ["TypeScript", "GraphQL", "PostgreSQL"],
                "description": "Join our fast-growing team..."
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudInc",
                "location": "Remote",
                "salary": "$140k - $170k",
                "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
                "preferred_skills": ["Python", "Go", "Terraform"],
                "description": "Build and maintain cloud infrastructure..."
            }
        ]
    
    def find_matching_jobs(self, skills: List[str], experience_years: int = 0) -> List[Dict]:
        """Find jobs matching user's skills"""
        matched_jobs = []
        
        for job in self.sample_jobs:
            # Calculate match score
            required_matches = set(skills) & set(job["required_skills"])
            preferred_matches = set(skills) & set(job["preferred_skills"])
            
            required_score = len(required_matches) / len(job["required_skills"]) * 60
            preferred_score = len(preferred_matches) / len(job["preferred_skills"]) * 40 if job["preferred_skills"] else 0
            
            total_score = required_score + preferred_score
            
            if total_score > 30:  # Only include jobs with >30% match
                job_copy = job.copy()
                job_copy["match_score"] = round(total_score, 1)
                job_copy["matching_skills"] = list(required_matches | preferred_matches)
                matched_jobs.append(job_copy)
        
        # Sort by match score
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return matched_jobs
    
    def get_skill_gap_analysis(self, user_skills: List[str], target_job: Dict) -> Dict:
        """Analyze what skills are missing for a target job"""
        required = set(target_job["required_skills"])
        preferred = set(target_job["preferred_skills"])
        user = set(user_skills)
        
        missing_required = required - user
        missing_preferred = preferred - user
        
        return {
            "missing_required": list(missing_required),
            "missing_preferred": list(missing_preferred),
            "has_required": len(required - missing_required) == len(required),
            "match_percentage": round((len(user & required) / len(required)) * 100, 1) if required else 0
        }