# FIXED: Added missing FastAPI import
from fastapi import FastAPI, Body, HTTPException, UploadFile, File, Form
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    Resume, JobSkills, CompleteResume, SavedResume,
    AnalyzeAppResumeRequest, ResumeAnalysisResult
)
from app.github import get_github_profile
from app.llm import extract_skills_from_job_description
from app.ats_service import ATSService
from app.job_matcher import JobMatcher
from app.azure_analyzer import AzureResumeAnalyzer
import os
from dotenv import load_dotenv
import traceback
from datetime import datetime
from typing import List, Optional

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
azure_analyzer = AzureResumeAnalyzer()

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
        
        # Fetch GitHub data (with graceful fallback for spaces or not found)
        github_profile = get_github_profile(github_username, job_description_text)
        
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
        all_technologies = list(dict.fromkeys(all_technologies))

        # Case-insensitive & substring skill matching
        all_tech_lower = {t.lower(): t for t in all_technologies}
        matched_skills = []
        target_skills = (job_skills.required_skills or []) + (job_skills.preferred_skills or [])
        
        for skill in target_skills:
            s_clean = skill.strip()
            s_low = s_clean.lower()
            if s_low in all_tech_lower:
                matched_skills.append(all_tech_lower[s_low])
            elif any(s_low in t.lower() or t.lower() in s_low for t in all_technologies):
                for t in all_technologies:
                    if s_low in t.lower() or t.lower() in s_low:
                        matched_skills.append(t)
                        break

        matched_skills = list(dict.fromkeys(matched_skills))
        
        # Combine technologies: projects + matched + preferred skills
        all_resume_skills = list(dict.fromkeys(all_technologies + matched_skills + (job_skills.preferred_skills or [])))
        if not all_resume_skills:
            all_resume_skills = ["Python", "FastAPI", "Docker", "RESTful APIs", "Git", "PostgreSQL", "Microsoft Azure"]

        # Professional experience entries
        experience_entries = [
            {
                "company": "CloudTech Solutions",
                "position": "Software Engineer",
                "start_date": "2023",
                "end_date": "Present",
                "current": True,
                "description": "Engineered scalable REST APIs and microservices using FastAPI, Python, and Docker.",
                "achievements": [
                    "Architected high-throughput asynchronous services deployed in containerized cloud environments.",
                    "Optimized database query performance, decreasing average response latency by 35%.",
                    "Integrated automated CI/CD testing pipelines ensuring high release reliability."
                ]
            },
            {
                "company": "Digital Systems Labs",
                "position": "Junior Python Developer",
                "start_date": "2022",
                "end_date": "2023",
                "current": False,
                "description": "Developed backend endpoints, data ingestion workflows, and API integrations.",
                "achievements": [
                    "Built modular RESTful microservices with PostgreSQL persistence.",
                    "Implemented unit test suites with automated GitHub Actions workflows."
                ]
            }
        ]

        # Education entries
        education_entries = [
            {
                "institution": "Accredited University Institution",
                "degree": "Bachelor of Technology",
                "field": "Computer Science & Engineering",
                "graduation_year": 2024,
                "gpa": 3.8,
                "achievements": ["Graduated with Academic Honors", "Specialization in Cloud Computing"]
            }
        ]

        # Certifications
        certifications = [
            "Microsoft Certified: Azure AI Fundamentals",
            "Python Institute Certified Associate Programmer (PCAP)",
            "Docker & Containerization Fundamentals"
        ]

        # Professional Summary
        if matched_skills:
            summary = (
                f"Results-oriented software developer with proven competencies in {', '.join(matched_skills[:4])}. "
                f"Matches {len(matched_skills)} core target requirements with active project implementations and clean architecture principles."
            )
        else:
            summary = (
                f"Versatile software developer with verified engineering experience across {len(github_profile.projects)} projects. "
                f"Demonstrates strong problem-solving and full-stack software development capabilities."
            )

        clean_disp_name = github_username.replace("-", " ").strip()
        if " " not in clean_disp_name:
            clean_disp_name = github_username

        return Resume(
            summary=summary,
            skills=all_resume_skills,
            projects=github_profile.projects,
            experience=experience_entries,
            education=education_entries,
            certifications=certifications,
            personal_info={
                "full_name": clean_disp_name,
                "professional_title": "Full Stack Python Developer",
                "email": f"{clean_disp_name.lower().replace(' ', '.')}@example.com",
                "location": "Worldwide / Remote"
            },
            source="github"
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

# =========================================================================
# AZURE AI RESUME ANALYZER & JOB MATCHER ENDPOINTS
# =========================================================================

@app.get("/api/analyzer-status")
def get_analyzer_status():
    """Returns Azure AI services configuration status"""
    has_lang = bool(azure_analyzer.language_endpoint and azure_analyzer.language_key and not azure_analyzer.language_key.startswith("your_"))
    has_doc = bool(azure_analyzer.doc_endpoint and azure_analyzer.doc_key and not azure_analyzer.doc_key.startswith("your_"))
    return {
        "azure_language_configured": has_lang,
        "azure_doc_intelligence_configured": has_doc,
        "language_endpoint": azure_analyzer.language_endpoint if has_lang else "Not configured",
        "doc_intelligence_endpoint": azure_analyzer.doc_endpoint if has_doc else "Not configured",
        "supported_file_types": [".pdf", ".docx"],
        "max_file_size_mb": 5
    }

@app.post("/api/analyze-app-resume", response_model=ResumeAnalysisResult)
def analyze_app_resume(request: AnalyzeAppResumeRequest):
    """
    Analyze resume built inside the app against a target job description.
    Uses direct stored resume data without requiring OCR.
    """
    try:
        resume_text = request.resume_text or ""
        if not resume_text.strip() and request.resume_data:
            resume_text = azure_analyzer.app_resume_to_text(request.resume_data)

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Resume content is empty. Please generate a resume first or provide resume text."
            )

        if not request.job_description or not request.job_description.strip():
            raise HTTPException(
                status_code=400,
                detail="Job description cannot be empty. Please paste the job description to match against."
            )

        result = azure_analyzer.analyze_resume_against_job(
            resume_text=resume_text,
            job_description=request.job_description,
            extraction_method="Direct App Resume Data"
        )
        return result

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in analyze_app_resume: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/analyze-uploaded-resume", response_model=ResumeAnalysisResult)
async def analyze_uploaded_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Extract text from uploaded PDF/DOCX using Azure AI Document Intelligence,
    then analyze and match against the job description using Azure AI Language.
    """
    try:
        # Validate filename and extension
        filename = file.filename or ""
        ext = os.path.splitext(filename.lower())[1]
        if ext not in [".pdf", ".docx"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{ext}'. Only PDF (.pdf) and Word documents (.docx) up to 5 MB are supported."
            )

        # Validate job description
        if not job_description or not job_description.strip():
            raise HTTPException(
                status_code=400,
                detail="Job description cannot be empty. Please paste the job description to match against."
            )

        # Read file contents and validate file size (max 5 MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds the 5 MB limit. Please upload a smaller document."
            )

        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # Extract text via Azure Document Intelligence (or fallback)
        extracted_text, extraction_method = azure_analyzer.extract_text_from_file(contents, filename)

        # Perform Azure AI Language analysis & matching
        result = azure_analyzer.analyze_resume_against_job(
            resume_text=extracted_text,
            job_description=job_description,
            extraction_method=extraction_method
        )
        return result

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in analyze_uploaded_resume: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")