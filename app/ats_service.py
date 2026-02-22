# app/ats_service.py
from typing import Dict, List

class ATSService:
    def analyze_ats_compatibility(self, resume_text: str) -> Dict:
        """
        Check if resume will pass Applicant Tracking Systems
        """
        # Common ATS keywords
        ats_keywords = [
            "achieved", "improved", "trained", "managed", 
            "created", "resolved", "volunteered", "increased",
            "decreased", "led", "developed", "implemented"
        ]
        
        # Check for issues
        issues = []
        suggestions = []
        score = 100
        
        # Check for action verbs
        found_keywords = [kw for kw in ats_keywords if kw.lower() in resume_text.lower()]
        if len(found_keywords) < 3:
            issues.append("Not enough action verbs")
            suggestions.append("Use more action verbs like 'achieved', 'implemented', 'developed'")
            score -= 20
        
        # Check length
        word_count = len(resume_text.split())
        if word_count < 300:
            issues.append("Resume too short")
            suggestions.append("Add more details about your experience")
            score -= 15
        elif word_count > 800:
            issues.append("Resume too long")
            suggestions.append("Keep it concise, max 2 pages")
            score -= 10
        
        # Check for contact info
        if "@" not in resume_text:
            issues.append("Missing email")
            suggestions.append("Add your email address")
            score -= 10
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "keyword_matches": found_keywords
        }
    
    def extract_keywords(self, job_description: str) -> List[str]:
        """Extract important keywords from job description"""
        words = job_description.lower().split()
        stop_words = ['the', 'and', 'for', 'with', 'have', 'will', 'can']
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return list(set(keywords))[:10]