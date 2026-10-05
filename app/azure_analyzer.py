import os
import re
import io
from typing import Dict, List, Tuple, Optional, Any
from difflib import SequenceMatcher
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Azure SDK Imports (safe fallback if not yet installed or missing credentials)
try:
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import HttpResponseError, ClientAuthenticationError, ServiceRequestError
    AZURE_CORE_AVAILABLE = True
except ImportError:
    AZURE_CORE_AVAILABLE = False
    HttpResponseError = Exception
    ClientAuthenticationError = Exception
    ServiceRequestError = Exception

try:
    from azure.ai.textanalytics import TextAnalyticsClient
    AZURE_TEXT_ANALYTICS_AVAILABLE = True
except ImportError:
    AZURE_TEXT_ANALYTICS_AVAILABLE = False

try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
    AZURE_DOC_INTEL_V4_AVAILABLE = True
except ImportError:
    AZURE_DOC_INTEL_V4_AVAILABLE = False

try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    AZURE_FORM_RECOGNIZER_AVAILABLE = True
except ImportError:
    AZURE_FORM_RECOGNIZER_AVAILABLE = False

# Local fallback parsers for PDF/DOCX
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class AzureResumeAnalyzer:
    """
    Core AI analyzer integrating Microsoft Azure AI Language & Document Intelligence
    with ATS scoring heuristics, skill matching, and resume quality audits.
    """

    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {".pdf", ".docx"}
    FUZZY_SKILL_THRESHOLD = 0.80  # 80% similarity threshold for fuzzy matching skills

    # Common technical skills and keywords database for NLP fallback & normalization
    CORE_SKILLS_TAXONOMY = {
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang", "rust",
        "ruby", "php", "swift", "kotlin", "sql", "nosql", "html", "css", "sass",
        "react", "react.js", "next.js", "vue", "angular", "node.js", "express",
        "fastapi", "flask", "django", "spring boot", "asp.net",
        "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "git", "github",
        "linux", "terraform", "ansible", "jenkins", "graphql", "rest", "restful api",
        "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
        "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
        "pytorch", "scikit-learn", "pandas", "numpy", "data analysis", "power bi", "tableau",
        "agile", "scrum", "microservices", "unit testing", "system design"
    }

    ATS_ACTION_VERBS = [
        "achieved", "analyzed", "architected", "automated", "built", "collaborated",
        "configured", "coordinated", "created", "debugged", "decreased", "delivered",
        "deployed", "designed", "developed", "directed", "documented", "engineered",
        "established", "executed", "formulated", "generated", "implemented", "improved",
        "increased", "initiated", "integrated", "launched", "led", "managed",
        "mentored", "migrated", "modeled", "monitored", "negotiated", "optimized",
        "orchestrated", "organized", "oversaw", "pioneered", "planned", "programmed",
        "reduced", "refactored", "resolved", "revamped", "scaled", "simplified",
        "spearheaded", "standardized", "strengthened", "supervised", "tested",
        "trained", "transformed", "troubleshot", "upgraded", "validated"
    ]

    def __init__(self):
        self.language_endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT", "").strip()
        self.language_key = os.getenv("AZURE_LANGUAGE_KEY", "").strip()
        self.doc_endpoint = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT", "").strip()
        self.doc_key = os.getenv("AZURE_DOC_INTELLIGENCE_KEY", "").strip()

    def get_language_client(self) -> Optional[Any]:
        """Returns initialized Azure TextAnalyticsClient if configured."""
        if not (AZURE_CORE_AVAILABLE and AZURE_TEXT_ANALYTICS_AVAILABLE):
            return None
        if self.language_endpoint and self.language_key and not self.language_key.startswith("your_"):
            try:
                return TextAnalyticsClient(
                    endpoint=self.language_endpoint,
                    credential=AzureKeyCredential(self.language_key)
                )
            except Exception as e:
                print(f"[AzureResumeAnalyzer] Error initializing TextAnalyticsClient: {e}")
        return None

    def get_document_client(self) -> Optional[Any]:
        """Returns initialized Azure Document Intelligence Client if configured."""
        if not AZURE_CORE_AVAILABLE:
            return None
        if not (self.doc_endpoint and self.doc_key and not self.doc_key.startswith("your_")):
            return None

        # Try v4 preview SDK first
        if AZURE_DOC_INTEL_V4_AVAILABLE:
            try:
                return DocumentIntelligenceClient(
                    endpoint=self.doc_endpoint,
                    credential=AzureKeyCredential(self.doc_key)
                )
            except Exception as e:
                print(f"[AzureResumeAnalyzer] Error initializing DocumentIntelligenceClient: {e}")

        # Fallback to formrecognizer SDK
        if AZURE_FORM_RECOGNIZER_AVAILABLE:
            try:
                return DocumentAnalysisClient(
                    endpoint=self.doc_endpoint,
                    credential=AzureKeyCredential(self.doc_key)
                )
            except Exception as e:
                print(f"[AzureResumeAnalyzer] Error initializing DocumentAnalysisClient: {e}")

        return None

    # =========================================================================
    # 1. TEXT EXTRACTION (Azure Document Intelligence + Local Fallbacks)
    # =========================================================================

    def extract_text_from_file(self, file_bytes: bytes, filename: str) -> Tuple[str, str]:
        """
        Extract text from uploaded PDF or DOCX resume.
        Returns: (extracted_text, extraction_method_status)
        """
        ext = os.path.splitext(filename.lower())[1]
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Only PDF and DOCX files are allowed.")

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("File size exceeds 5 MB limit. Please upload a smaller resume document.")

        # Attempt Azure AI Document Intelligence extraction
        doc_client = self.get_document_client()
        if doc_client:
            try:
                # Document Intelligence v4 SDK
                if AZURE_DOC_INTEL_V4_AVAILABLE and isinstance(doc_client, DocumentIntelligenceClient):
                    poller = doc_client.begin_analyze_document(
                        model_id="prebuilt-read",
                        analyze_request=file_bytes,
                        content_type="application/octet-stream"
                    )
                    result = poller.result()
                    extracted_text = result.content or ""
                    if extracted_text.strip():
                        return extracted_text.strip(), "Azure AI Document Intelligence (prebuilt-read)"

                # Form Recognizer v3 SDK
                elif AZURE_FORM_RECOGNIZER_AVAILABLE and isinstance(doc_client, DocumentAnalysisClient):
                    poller = doc_client.begin_analyze_document(
                        model_id="prebuilt-read",
                        document=file_bytes
                    )
                    result = poller.result()
                    extracted_text = result.content or ""
                    if extracted_text.strip():
                        return extracted_text.strip(), "Azure AI Document Intelligence (prebuilt-read)"
            except HttpResponseError as http_err:
                status_code = getattr(http_err, "status_code", 500)
                if status_code == 429:
                    print("[AzureResumeAnalyzer] Azure Document Intelligence rate limit reached (429). Falling back to local OCR parser.")
                else:
                    print(f"[AzureResumeAnalyzer] Azure Document Intelligence HTTP error ({status_code}): {http_err.message}. Falling back.")
            except Exception as e:
                print(f"[AzureResumeAnalyzer] Azure Document Intelligence error: {e}. Falling back to local parser.")

        # Fallback to local parsing (PyPDF2 / python-docx)
        text = ""
        if ext == ".pdf":
            text = self._extract_pdf_local(file_bytes)
            status = "Local PDF Engine (Configure Azure Doc Intelligence in .env for advanced layout OCR)"
        elif ext == ".docx":
            text = self._extract_docx_local(file_bytes)
            status = "Local DOCX Engine (Configure Azure Doc Intelligence in .env for advanced layout OCR)"

        if not text.strip():
            raise ValueError("Could not extract any readable text from the uploaded file. Please ensure it is not scanned image-only or password-protected.")

        return text.strip(), status

    def _extract_pdf_local(self, file_bytes: bytes) -> str:
        if not PYPDF2_AVAILABLE:
            raise ValueError("PyPDF2 is not installed. Please install PyPDF2 or configure Azure Document Intelligence.")
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)

    def _extract_docx_local(self, file_bytes: bytes) -> str:
        if not DOCX_AVAILABLE:
            raise ValueError("python-docx is not installed. Please install python-docx or configure Azure Document Intelligence.")
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        return "\n".join(paragraphs)

    def app_resume_to_text(self, resume_data: Any) -> str:
        """
        Converts app-built resume data (dict or CompleteResume or Resume schema)
        into a clean, structured text representation.
        """
        if isinstance(resume_data, str):
            return resume_data

        if not isinstance(resume_data, dict):
            if hasattr(resume_data, "dict"):
                resume_data = resume_data.dict()
            elif hasattr(resume_data, "model_dump"):
                resume_data = resume_data.model_dump()
            else:
                return str(resume_data)

        lines = []

        # Personal Info
        personal = resume_data.get("personal_info") or {}
        if personal:
            name = personal.get("full_name") or ""
            email = personal.get("email") or ""
            phone = personal.get("phone") or ""
            location = personal.get("location") or ""
            title = personal.get("professional_title") or ""
            linkedin = personal.get("linkedin") or ""
            portfolio = personal.get("portfolio") or ""
            header_items = [item for item in [name, title, email, phone, location, linkedin, portfolio] if item]
            if header_items:
                lines.append("CONTACT INFORMATION\n" + " | ".join(header_items))

        # Summary
        summary = resume_data.get("summary") or ""
        if summary:
            lines.append(f"\nPROFESSIONAL SUMMARY\n{summary}")

        # Skills
        skills = resume_data.get("skills")
        if isinstance(skills, list):
            lines.append("\nTECHNICAL SKILLS\n" + ", ".join(skills))
        elif isinstance(skills, dict):
            all_cat_skills = []
            for category, skill_list in skills.items():
                if isinstance(skill_list, list) and skill_list:
                    all_cat_skills.append(f"{category.title()}: {', '.join(skill_list)}")
            if all_cat_skills:
                lines.append("\nTECHNICAL SKILLS\n" + "\n".join(all_cat_skills))

        # Work Experience
        experience = resume_data.get("experience") or []
        if isinstance(experience, list) and experience:
            lines.append("\nWORK EXPERIENCE")
            for exp in experience:
                comp = exp.get("company", "")
                pos = exp.get("position", "")
                desc = exp.get("description", "")
                achievements = exp.get("achievements") or []
                dates = f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present' if exp.get('current') else '')}"
                lines.append(f"• {pos} at {comp} ({dates})\n  {desc}")
                for ach in achievements:
                    lines.append(f"  - {ach}")

        # Projects / GitHub Projects
        projects = resume_data.get("projects") or resume_data.get("github_projects") or []
        if isinstance(projects, list) and projects:
            lines.append("\nPROJECTS")
            for proj in projects:
                name = proj.get("name", "")
                desc = proj.get("description", "")
                techs = proj.get("technologies") or []
                tech_str = f" [Technologies: {', '.join(techs)}]" if techs else ""
                lines.append(f"• {name}{tech_str}: {desc}")

        # Education
        education = resume_data.get("education") or []
        if isinstance(education, list) and education:
            lines.append("\nEDUCATION")
            for edu in education:
                inst = edu.get("institution", "")
                deg = edu.get("degree", "")
                field = edu.get("field", "")
                grad = edu.get("graduation_year", "")
                lines.append(f"• {deg} in {field} - {inst} ({grad})")

        # Certifications
        certs = resume_data.get("certifications") or []
        if isinstance(certs, list) and certs:
            lines.append("\nCERTIFICATIONS\n" + ", ".join(certs))

        return "\n".join(lines).strip()

    # =========================================================================
    # 2. INFORMATION & ENTITY EXTRACTION (Azure AI Language + Fallbacks)
    # =========================================================================

    def extract_entities_and_phrases(self, text: str) -> Tuple[Dict[str, List[str]], str]:
        """
        Uses Azure AI Language (Text Analytics) to extract:
        - Skills
        - Job titles
        - Organizations
        - Education
        - Key phrases
        Returns: (extracted_data_dict, service_status_string)
        """
        client = self.get_language_client()
        status_msg = "Azure AI Language Service (NER + Key Phrase Extraction)"

        if client:
            try:
                # Text Analytics allows up to 5120 characters per document in free tier
                chunk = text[:5000]
                entities_resp = client.recognize_entities(documents=[chunk])[0]
                phrases_resp = client.extract_key_phrases(documents=[chunk])[0]

                skills = []
                job_titles = []
                organizations = []
                education = []

                if not entities_resp.is_error:
                    for ent in entities_resp.entities:
                        cat = (ent.category or "").lower()
                        subcat = (ent.subcategory or "").lower()
                        val = ent.text.strip()
                        if not val or len(val) < 2:
                            continue

                        if cat == "skill" or subcat == "skill":
                            skills.append(val)
                        elif cat in ["jobtitle", "persontype"] or subcat in ["jobtitle", "persontype"]:
                            job_titles.append(val)
                        elif cat == "organization":
                            organizations.append(val)
                        elif "degree" in cat or "education" in cat or "degree" in subcat:
                            education.append(val)

                key_phrases = []
                if not phrases_resp.is_error:
                    key_phrases = [p for p in phrases_resp.key_phrases if len(p) > 2]

                # Augment with domain taxonomy scan to ensure no common programming skill is missed
                supplemental_skills = self._extract_skills_rule_based(text)
                merged_skills = self._deduplicate_list(skills + supplemental_skills)

                return {
                    "skills": merged_skills,
                    "job_titles": self._deduplicate_list(job_titles),
                    "organizations": self._deduplicate_list(organizations),
                    "education": self._deduplicate_list(education),
                    "key_phrases": self._deduplicate_list(key_phrases)[:25]
                }, status_msg

            except HttpResponseError as http_err:
                status_code = getattr(http_err, "status_code", 500)
                if status_code == 429:
                    status_msg = "Azure AI Language: Rate limit reached (429). Using intelligent NLP fallback."
                    print("[AzureResumeAnalyzer] Azure AI Language Rate Limit hit.")
                else:
                    status_msg = f"Azure AI Language HTTP {status_code}: Using intelligent NLP fallback."
                    print(f"[AzureResumeAnalyzer] Azure AI Language HTTP error: {http_err.message}")
            except Exception as e:
                status_msg = f"Azure AI Language notice: {str(e)[:60]}... Using intelligent NLP fallback."
                print(f"[AzureResumeAnalyzer] Azure AI Language exception: {e}")
        else:
            status_msg = "Intelligent NLP Engine (Configure Azure Language Endpoint & Key in .env for Azure Cloud NER)"

        # Fallback heuristic entity & skill extraction
        fallback_data = self._extract_entities_fallback(text)
        return fallback_data, status_msg

    def _extract_skills_rule_based(self, text: str) -> List[str]:
        """Scans text against core technology taxonomy."""
        text_lower = f" {text.lower()} "
        found = []
        for skill in self.CORE_SKILLS_TAXONOMY:
            pattern = r'(?<![a-zA-Z0-9#+])' + re.escape(skill) + r'(?![a-zA-Z0-9#+])'
            if re.search(pattern, text_lower):
                found.append(skill.title() if not skill.isupper() else skill)
        return found

    def _extract_entities_fallback(self, text: str) -> Dict[str, List[str]]:
        """Fallback NLP parser when Azure Language credentials are not supplied."""
        skills = self._extract_skills_rule_based(text)

        # Extract Job Titles heuristics
        common_titles = [
            "software engineer", "frontend developer", "backend developer",
            "full stack developer", "full stack engineer", "python developer",
            "data scientist", "devops engineer", "cloud architect",
            "machine learning engineer", "product manager", "qa engineer",
            "system administrator", "mobile developer", "solutions architect"
        ]
        text_lower = text.lower()
        job_titles = [title.title() for title in common_titles if title in text_lower]

        # Extract organizations heuristic
        org_matches = re.findall(r'\b([A-Z][a-zA-Z0-9]+(?:\s+(?:Inc|LLC|Corp|Technologies|Labs|Systems|Solutions|Software|Services))\b)', text)
        organizations = [m.strip() for m in org_matches][:5]

        # Extract education heuristic
        edu_keywords = ["bachelor", "master", "phd", "b.tech", "b.e.", "m.tech", "m.s.", "b.s.", "computer science", "information technology"]
        education = [k.title() for k in edu_keywords if k in text_lower]

        # Extract key phrases (frequent multi-word candidate tokens)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {"the", "and", "for", "with", "from", "that", "this", "have", "will", "your", "work", "team", "year", "years"}
        filtered_words = [w for w in words if w not in stopwords]
        
        # Word frequency to select top terms
        word_freq: Dict[str, int] = {}
        for w in filtered_words:
            word_freq[w] = word_freq.get(w, 0) + 1
        
        top_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        key_phrases = [t[0].title() for t in top_terms]

        return {
            "skills": skills,
            "job_titles": job_titles,
            "organizations": organizations,
            "education": education,
            "key_phrases": key_phrases
        }

    # =========================================================================
    # 3. MATCHING ENGINE & SCORE COMPUTATION (0-100)
    # =========================================================================

    def calculate_match_score(
        self,
        resume_text: str,
        resume_entities: Dict[str, List[str]],
        job_text: str,
        job_entities: Dict[str, List[str]]
    ) -> Tuple[int, Dict[str, float], List[str], List[str]]:
        """
        Calculates match score between resume and job description.
        Returns: (overall_score, score_breakdown, matched_skills, missing_skills)
        """
        resume_text_lower = resume_text.lower()
        job_skills = job_entities.get("skills", [])
        resume_skills = resume_entities.get("skills", [])

        # If job description had no explicit skills detected, run taxonomy scan on it
        if not job_skills:
            job_skills = self._extract_skills_rule_based(job_text)
            if not job_skills:
                # Extract significant technical words from job
                job_skills = [kp for kp in job_entities.get("key_phrases", []) if len(kp) > 3][:8]

        resume_skills_set = {s.lower() for s in resume_skills}
        matched_skills_list = []
        missing_skills_list = []

        for skill in job_skills:
            skill_clean = skill.strip()
            skill_lower = skill_clean.lower()
            pattern = r'(?<![a-zA-Z0-9#+])' + re.escape(skill_lower) + r'(?![a-zA-Z0-9#+])'
            
            # Match 1: Exact match in extracted resume skills or regex word-boundary in resume text
            is_exact = (skill_lower in resume_skills_set) or bool(re.search(pattern, resume_text_lower))
            
            # Match 2: Fuzzy similarity above threshold (0.80) against any resume skill
            is_fuzzy = False
            if not is_exact:
                for rs in resume_skills_set:
                    if SequenceMatcher(None, skill_lower, rs).ratio() >= self.FUZZY_SKILL_THRESHOLD:
                        is_fuzzy = True
                        break

            if is_exact or is_fuzzy:
                matched_skills_list.append(skill_clean)
            else:
                missing_skills_list.append(skill_clean)

        matched_skills_list = self._deduplicate_list(matched_skills_list)
        missing_skills_list = self._deduplicate_list(missing_skills_list)

        # 1. Skills score (45% weight)
        total_job_skills_count = len(matched_skills_list) + len(missing_skills_list)
        if total_job_skills_count > 0:
            skills_score = (len(matched_skills_list) / total_job_skills_count) * 100.0
        else:
            skills_score = 75.0  # neutral baseline if job desc has no specific skill tags

        # 2. Keywords / Key phrases Jaccard similarity score (25% weight)
        # J(A, B) = |A ∩ B| / |A ∪ B|, where A = resume key phrases, B = job key phrases
        resume_phrases = {kp.lower().strip() for kp in resume_entities.get("key_phrases", []) if len(kp.strip()) > 2}
        job_phrases = {kp.lower().strip() for kp in job_entities.get("key_phrases", []) if len(kp.strip()) > 2}

        if job_phrases:
            matched_p = {p for p in job_phrases if p in resume_phrases or p in resume_text_lower}
            union_phrases = job_phrases | resume_phrases
            if union_phrases:
                jaccard_val = len(matched_p) / len(union_phrases)
                keywords_score = min(100.0, max(0.0, jaccard_val * 100.0 * 2.0))
                if not resume_phrases:
                    keywords_score = (len(matched_p) / len(job_phrases)) * 100.0
            else:
                keywords_score = 70.0
        else:
            keywords_score = 75.0

        # 3. Experience / Role relevance score (20% weight)
        # Weighting: Base = 20 pts, Target Title = 40 pts, Seniority terms = 20 pts, Leadership keywords = 20 pts (Max: 100)
        experience_score = 20.0  # Base professional experience
        resume_titles = {t.lower() for t in resume_entities.get("job_titles", [])}
        job_titles = [t.lower() for t in job_entities.get("job_titles", [])]

        # Target job title match (40 points)
        if any(jt in resume_text_lower or jt in resume_titles for jt in job_titles) or len(resume_titles) > 0:
            experience_score += 40.0

        # Seniority terms check (20 points): senior, lead, principal, architect, staff
        seniority_terms = ["senior", "lead", "principal", "architect", "staff", "head"]
        if any(re.search(r'\b' + re.escape(term) + r'\b', resume_text_lower) for term in seniority_terms):
            experience_score += 20.0

        # Leadership & impact keywords check (20 points): managed, led, directed, spearheaded, mentored
        leadership_terms = ["managed", "led", "directed", "spearheaded", "mentored", "orchestrated", "supervised", "coordinated"]
        if any(re.search(r'\b' + re.escape(term) + r'\b', resume_text_lower) for term in leadership_terms):
            experience_score += 20.0

        experience_score = min(100.0, experience_score)

        # 4. Education / Credentials score (10% weight)
        # Points: PhD = 100, Master's = 90, Bachelor's = 80, Associate = 70, Relevant STEM = 60, Base = 50
        resume_edu_texts = " ".join(resume_entities.get("education", [])).lower() + " " + resume_text_lower

        if any(d in resume_edu_texts for d in ["phd", "ph.d", "doctorate", "doctor of philosophy"]):
            education_score = 100.0
        elif any(d in resume_edu_texts for d in ["master", "m.s.", "m.tech", "mba", "msc", "m.e."]):
            education_score = 90.0
        elif any(d in resume_edu_texts for d in ["bachelor", "b.s.", "b.tech", "b.e.", "bsc", "undergraduate"]):
            education_score = 80.0
        elif any(d in resume_edu_texts for d in ["associate", "diploma"]):
            education_score = 70.0
        elif any(d in resume_edu_texts for d in ["computer science", "information technology", "engineering", "degree", "university"]):
            education_score = 60.0
        else:
            education_score = 50.0

        # Weighted calculation
        overall_score = (
            (skills_score * 0.45) +
            (keywords_score * 0.25) +
            (experience_score * 0.20) +
            (education_score * 0.10)
        )
        overall_score = max(5, min(100, int(round(overall_score))))

        score_breakdown = {
            "skills_score": round(skills_score, 1),
            "keywords_score": round(keywords_score, 1),
            "experience_score": round(experience_score, 1),
            "education_score": round(education_score, 1)
        }

        return overall_score, score_breakdown, matched_skills_list, missing_skills_list

    # =========================================================================
    # 4. RESUME QUALITY & ATS READINESS CHECKS
    # =========================================================================

    def check_resume_quality(
        self,
        resume_text: str,
        resume_entities: Dict[str, List[str]],
        missing_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Audits key sections, contact information, length, and action verb strength.
        Returns actionable quality findings and recommendations.
        """
        text_lower = resume_text.lower()
        suggestions: List[str] = []

        # 1. Section presence checks
        sections_detected = {
            "summary": bool(re.search(r'\b(summary|objective|profile|about me|about)\b', text_lower)),
            "skills": bool(re.search(r'\b(skills|technologies|technical stack|competencies)\b', text_lower)),
            "experience": bool(re.search(r'\b(experience|employment|work history|professional background)\b', text_lower)),
            "education": bool(re.search(r'\b(education|academic|degree|university|college)\b', text_lower)),
            "projects": bool(re.search(r'\b(projects|portfolio|personal projects|github projects)\b', text_lower)),
        }

        for sec, present in sections_detected.items():
            if not present:
                suggestions.append(f"Add a distinct '{sec.title()}' section to improve ATS structure and reader clarity.")

        # 2. Contact info presence
        email_present = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text))
        phone_present = bool(re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text))
        linkedin_present = bool("linkedin.com" in text_lower)
        github_present = bool("github.com" in text_lower)

        contact_info = {
            "email": email_present,
            "phone": phone_present,
            "linkedin": linkedin_present,
            "github": github_present
        }

        if not email_present:
            suggestions.append("Missing email address: Ensure recruiters can contact you by adding your email at the top.")
        if not phone_present:
            suggestions.append("Missing phone number: Add a contact number with country code.")
        if not (linkedin_present or github_present):
            suggestions.append("Add professional links (LinkedIn profile or GitHub URL) to validate your work.")

        # 3. Word count & length
        words = resume_text.split()
        word_count = len(words)

        if word_count < 250:
            suggestions.append(f"Resume is concise ({word_count} words). Elaborate on achievements, measurable impacts, and responsibilities (aim for 350-700 words).")
        elif word_count > 950:
            suggestions.append(f"Resume is lengthy ({word_count} words). Consider condensing details to keep it within a sharp 1-2 page format.")

        # 4. Action verbs analysis
        found_action_verbs = []
        for verb in self.ATS_ACTION_VERBS:
            pattern = r'\b' + re.escape(verb) + r'\b'
            if re.search(pattern, text_lower):
                found_action_verbs.append(verb)

        found_action_verbs = self._deduplicate_list(found_action_verbs)
        if len(found_action_verbs) < 4:
            suggestions.append(f"Incorporate more strong ATS action verbs (e.g., 'orchestrated', 'engineered', 'spearheaded', 'optimized') to highlight your contributions.")

        # 5. Missing skills recommendation
        if missing_skills:
            top_missing = missing_skills[:4]
            suggestions.append(f"High-priority missing skills for this role: {', '.join(top_missing)}. Include them if you have relevant experience.")

        # Overall quality tier
        if len(suggestions) <= 1:
            overall_quality = "Excellent"
        elif len(suggestions) <= 3:
            overall_quality = "Good"
        elif len(suggestions) <= 5:
            overall_quality = "Fair"
        else:
            overall_quality = "Needs Attention"

        return {
            "overall_quality": overall_quality,
            "sections_detected": sections_detected,
            "contact_info": contact_info,
            "word_count": word_count,
            "action_verbs_found": found_action_verbs[:12],
            "suggestions": suggestions
        }

    # =========================================================================
    # 5. FULL PIPELINE EXECUTION
    # =========================================================================

    def analyze_resume_against_job(
        self,
        resume_text: str,
        job_description: str,
        extraction_method: str = "Direct Resume Data"
    ) -> Dict[str, Any]:
        """
        Executes complete end-to-end analysis:
        1. Entity extraction on Resume and Job Description via Azure AI Language
        2. Match score computation
        3. Quality checks
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text is empty. Please provide resume data or upload a file.")

        if not job_description or not job_description.strip():
            raise ValueError("Job description is empty. Please paste the target job description.")

        # 1. Entity and phrase extraction
        resume_data, lang_status_resume = self.extract_entities_and_phrases(resume_text)
        job_data, lang_status_job = self.extract_entities_and_phrases(job_description)

        # 2. Match scoring
        overall_score, breakdown, matched_skills, missing_skills = self.calculate_match_score(
            resume_text=resume_text,
            resume_entities=resume_data,
            job_text=job_description,
            job_entities=job_data
        )

        # 3. Quality audit
        quality_report = self.check_resume_quality(
            resume_text=resume_text,
            resume_entities=resume_data,
            missing_skills=missing_skills
        )

        return {
            "status": "success",
            "overall_score": overall_score,
            "score_breakdown": breakdown,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "quality_report": quality_report,
            "extracted_resume_data": resume_data,
            "extracted_job_data": job_data,
            "azure_service_status": {
                "document_intelligence": extraction_method,
                "language_service": lang_status_resume
            },
            "message": "Analysis completed successfully."
        }

    @staticmethod
    def _deduplicate_list(items: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for item in items:
            cleaned = item.strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                deduped.append(cleaned)
        return deduped
