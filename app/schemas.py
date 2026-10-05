from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# Used for extracting skills from job description
class JobSkills(BaseModel):
    required_skills: List[str]
    preferred_skills: List[str]


# GitHub project info
class Project(BaseModel):
    name: str
    description: str
    technologies: List[str]


# GitHub profile data
class GitHubProfile(BaseModel):
    username: str
    projects: List[Project]


# API request body
class JobDescription(BaseModel):
    github_username: str
    job_description_text: str


# Final resume response
class Resume(BaseModel):
    summary: str
    skills: List[str]
    projects: List[Project]


# Your existing code (keep this)...
class JobSkills(BaseModel):
    required_skills: List[str]
    preferred_skills: List[str]

class Project(BaseModel):
    name: str
    description: str
    technologies: List[str]

class GitHubProfile(BaseModel):
    username: str
    projects: List[Project]

class JobDescription(BaseModel):
    github_username: str
    job_description_text: str

class Resume(BaseModel):
    summary: str
    skills: List[str]
    projects: List[Project]
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    personal_info: Optional[Dict[str, Any]] = None
    source: Optional[str] = "github"

# ===========================================
# 👇 ADD THESE NEW MODELS BELOW THIS LINE
# ===========================================

# Personal Information
class PersonalInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    portfolio: str = ""
    professional_title: str = ""

# Work Experience
class WorkExperience(BaseModel):
    company: str = ""
    position: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    description: str = ""
    achievements: List[str] = []

# Education
class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    achievements: List[str] = []

# Categorized Skills
class CategorizedSkills(BaseModel):
    technical: List[str] = []
    frameworks: List[str] = []
    tools: List[str] = []
    soft_skills: List[str] = []
    languages: List[str] = []

# Complete Resume with all sections
class CompleteResume(BaseModel):
    personal_info: PersonalInfo = PersonalInfo()
    summary: str = ""
    experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: CategorizedSkills = CategorizedSkills()
    github_projects: List[Project] = []
    certifications: List[str] = []
    
# For database storage
class SavedResume(BaseModel):
    id: Optional[str] = None
    user_id: str = ""
    name: str = ""
    created_at: str = ""
    updated_at: str = ""
    resume_data: CompleteResume
    template: str = "modern"

# ===========================================
# Azure AI Resume Analyzer Models
# ===========================================

class ScoreBreakdown(BaseModel):
    skills_score: float = 0.0
    keywords_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0

class QualityCheckResult(BaseModel):
    overall_quality: str = "Good"
    sections_detected: Dict[str, bool] = {}
    contact_info: Dict[str, bool] = {}
    word_count: int = 0
    action_verbs_found: List[str] = []
    suggestions: List[str] = []

class ExtractedEntities(BaseModel):
    skills: List[str] = []
    job_titles: List[str] = []
    organizations: List[str] = []
    education: List[str] = []
    key_phrases: List[str] = []

class ResumeAnalysisResult(BaseModel):
    status: str = "success"
    overall_score: int = 0
    score_breakdown: ScoreBreakdown = ScoreBreakdown()
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    quality_report: QualityCheckResult = QualityCheckResult()
    extracted_resume_data: ExtractedEntities = ExtractedEntities()
    extracted_job_data: ExtractedEntities = ExtractedEntities()
    azure_service_status: Dict[str, str] = {}
    message: Optional[str] = None

class AnalyzeAppResumeRequest(BaseModel):
    resume_data: Optional[Dict] = None
    resume_text: Optional[str] = None
    job_description: str