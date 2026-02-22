# FIXED: Added missing FastAPI import
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import Resume, JobSkills, CompleteResume, SavedResume
from app.github import get_github_profile
from app.llm import extract_skills_from_job_description
from app.ats_service import ATSService
from app.job_matcher import JobMatcher
import os
from dotenv import load_dotenv
import traceback
from datetime import datetime
from typing import List

load_dotenv()

app = FastAPI(title="Intelligent Resume Builder API")

# FIXED: CORS middleware moved to correct position (before routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ats_service = ATSService()
job_matcher = JobMatcher()

# Serve static files (if you have CSS/JS files)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    """Serve the HTML UI"""
    return FileResponse("index.html")

@app.get("/docs-redirect")
def docs_redirect():
    return RedirectResponse(url="/docs")

# FIXED: Removed duplicate generate_resume endpoint - keeping only one
@app.post("/generate_resume", response_model=Resume)
def generate_resume(
    github_username: str = Body(..., embed=True),
    job_description_text: str = Body(..., embed=True)
):
    try:
        print(f"Generating resume for: {github_username}")
        
        # Fetch GitHub data
        github_profile = get_github_profile(github_username)
        
        # Extract skills from job description
        try:
            job_skills = extract_skills_from_job_description(job_description_text)
        except Exception as e:
            job_skills = JobSkills(required_skills=[], preferred_skills=[])
            print(f"LLM error: {e}")

        # Get all technologies from projects
        all_technologies = []
        for project in github_profile.projects:
            all_technologies.extend(project.technologies)
        
        all_technologies = list(set(all_technologies))

        # Match skills
        matched_skills = list(
            set(job_skills.required_skills).intersection(all_technologies)
        )

        # Build summary
        if matched_skills:
            summary = f"🎯 {github_username} matches {len(matched_skills)} skills: {', '.join(matched_skills)}"
        else:
            summary = f"📊 {github_username} has {len(github_profile.projects)} public repositories. Try a more specific job description!"

        return Resume(
            summary=summary,
            skills=matched_skills + job_skills.preferred_skills,
            projects=github_profile.projects
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# NEW ENDPOINTS
# ===========================================

@app.post("/generate_complete_resume")
def generate_complete_resume(resume_data: CompleteResume):
    """Generate a complete resume with all sections"""
    try:
        return {
            "status": "success",
            "message": "Resume generated successfully",
            "data": resume_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_ats")
def analyze_ats(resume_text: str = Body(..., embed=True)):
    """Analyze resume for ATS compatibility"""
    try:
        result = ats_service.analyze_ats_compatibility(resume_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/find_matching_jobs")
def find_matching_jobs(
    skills: List[str] = Body(...),
    experience_years: int = Body(0)
):
    """Find jobs matching your skills"""
    try:
        jobs = job_matcher.find_matching_jobs(skills, experience_years)
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/skill_gap_analysis")
def skill_gap_analysis(
    user_skills: List[str] = Body(...),
    target_job_title: str = Body(...)
):
    """Analyze skill gaps for a target job"""
    try:
        # Find the target job
        target_job = None
        for job in job_matcher.sample_jobs:
            if job["title"].lower() == target_job_title.lower():
                target_job = job
                break
        
        if not target_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        analysis = job_matcher.get_skill_gap_analysis(user_skills, target_job)
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_resume")
def save_resume(resume: SavedResume):
    """Save resume to database (mock implementation)"""
    try:
        # In real app, you'd save to database
        resume.id = datetime.now().strftime("%Y%m%d%H%M%S")
        resume.created_at = datetime.now().isoformat()
        resume.updated_at = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Resume saved successfully",
            "id": resume.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
def get_templates():
    """Get available resume templates"""
    templates = [
        {
            "id": "modern",
            "name": "Modern",
            "description": "Clean and contemporary design",
            "preview": "/template-preview/modern"
        },
        {
            "id": "professional",
            "name": "Professional",
            "description": "Traditional corporate style",
            "preview": "/template-preview/professional"
        },
        {
            "id": "creative",
            "name": "Creative",
            "description": "For designers and artists",
            "preview": "/template-preview/creative"
        },
        {
            "id": "technical",
            "name": "Technical",
            "description": "Focus on skills and projects",
            "preview": "/template-preview/technical"
        }
    ]
    return {"templates": templates}

@app.get("/template-preview/{template_name}")
def get_template_preview(template_name: str):
    """Serve template preview HTML files"""
    template_file = f"static/templates/{template_name}.html"
    if os.path.exists(template_file):
        return FileResponse(template_file)
    else:
        raise HTTPException(status_code=404, detail="Template not found")

@app.get("/debug")
def debug():
    """Debug endpoint to see all routes"""
    return {
        "routes": [
            {
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            }
            for route in app.routes
        ]
    }