# Intelligent Resume Builder & Azure AI Analyzer

An intelligent, full-stack application that generates professional resumes from GitHub repositories and analyzes resumes against job descriptions using **Microsoft Azure AI Services** (Azure AI Document Intelligence & Azure AI Language) and AI/ML algorithms.

---

## 🚀 Key Features

1. **AI Resume Generator (GitHub Integration)**:
   - Fetches public repositories, languages, and project metadata directly from GitHub API.
   - Tailors project descriptions and skills to a target job description.
   - Live template switcher (Modern, Professional, Creative, Technical) with instant PDF export.

2. **Azure AI Resume Analyzer & Job Matcher**:
   - **Dual Input Modes**:
     - Analyze resumes generated directly inside the application.
     - Upload existing resumes in PDF or Word (`.docx`) format (up to 5 MB, validated).
   - **Text & Layout Extraction**:
     - Powered by **Azure AI Document Intelligence** (`prebuilt-read` model) to extract structured text, tables, and paragraphs from uploaded resumes.
   - **Information & Entity Extraction**:
     - Powered by **Azure AI Language (Text Analytics)** for Named Entity Recognition (NER: Skills, Job Titles, Organizations, Education) and Key Phrase Extraction.
   - **Intelligent Match Engine (0–100 Score)**:
     - Weighted scoring algorithm:
       - **Skills Overlap (45% weight)**: Compares required and preferred technologies.
       - **Keywords & Domain Terms (25% weight)**: Jaccard overlap of key phrases.
       - **Experience & Role Relevance (20% weight)**: Matches target roles, seniorities, and responsibilities.
       - **Education & Credentials (10% weight)**: Recognizes degrees and relevant fields.
     - Returns matched skills chips (green) and missing skills chips (red).
   - **ATS Resume Quality Audit**:
     - Section presence check (Summary, Skills, Experience, Education, Projects).
     - Contact details check (Email, Phone, LinkedIn, GitHub).
     - Optimal length analysis (word count heuristics).
     - ATS action verbs scanner (e.g., *orchestrated*, *spearheaded*, *engineered*).
     - Actionable AI-driven improvement suggestions.
   - **Interactive UI**:
     - Clean tabbed interface matching the existing design.
     - Animated SVG circular match score gauge with color dynamics.
     - "Edit resume" navigation button returning directly to the builder.
     - Graceful offline fallback and friendly Azure rate-limit handling.

---

## 🛠️ Technology Stack & AI/ML Architecture

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.10+ / FastAPI, Uvicorn, Pydantic |
| **Cloud AI Services** | **Microsoft Azure AI Language** (`azure-ai-textanalytics`)<br>**Azure AI Document Intelligence** (`azure-ai-documentintelligence`) |
| **AI / NLP Methods** | Named Entity Recognition (NER), Key Phrase Extraction, ATS Action Verb Heuristics, Weighted Cosine/Jaccard Token Overlap |
| **Frontend** | HTML5, Tailwind CSS, Font Awesome, Animate.css, jsPDF |
| **Document Processing** | PyPDF2, python-docx, Document Intelligence OCR |

---

## ☁️ Azure Resources Setup (Free F0 Tier)

You can run this project using Microsoft Azure's **Free Tier (F0)**:

### 1. Azure AI Language Service (Free F0)
- In [Azure Portal](https://portal.azure.com/), create a resource: **Language Service**.
- Select the **Free F0** pricing tier (5,000 text records per month).
- Under **Resource Management** -> **Keys and Endpoint**, copy:
  - `AZURE_LANGUAGE_ENDPOINT`
  - `AZURE_LANGUAGE_KEY`

### 2. Azure AI Document Intelligence (Free F0)
- In Azure Portal, create a resource: **Document Intelligence** (formerly Form Recognizer).
- Select the **Free F0** pricing tier (500 pages per month).
- Under **Resource Management** -> **Keys and Endpoint**, copy:
  - `AZURE_DOC_INTELLIGENCE_ENDPOINT`
  - `AZURE_DOC_INTELLIGENCE_KEY`

> **Note**: If Azure keys are not yet configured, the analyzer automatically engages intelligent built-in NLP heuristics and local document parsers, providing zero-crash execution and helpful guidance.

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root (see `.env.example`):

```env
# Microsoft Azure AI Language
AZURE_LANGUAGE_ENDPOINT=https://<your-language-resource>.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=your_azure_language_key_here

# Microsoft Azure AI Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://<your-doc-intel-resource>.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=your_azure_doc_intelligence_key_here

# Optional: OpenAI API Key (for legacy prompt generator)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: GitHub Personal Access Token (for higher API rate limits)
GITHUB_TOKEN=your_github_token_here
```

---

## 📦 Installation & Running

### 1. Clone & Install Dependencies
```bash
# Navigate to the project directory
cd intelligent-resume-builder-api

# Create and activate virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate # On macOS/Linux

# Install requirements
pip install -r requirements.txt
```

### 2. Start the FastAPI Application
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser and visit: **`http://127.0.0.1:8000`**

Interactive API Swagger documentation is available at: **`http://127.0.0.1:8000/docs`**

---

## 🧪 Running Unit Tests

Run the test suite verifying scoring algorithms, entity matching, and quality checks:

```bash
# Using standard Python unittest (works out-of-the-box):
python -m unittest discover -s tests

# Or using pytest (if installed):
python -m pytest tests/ -v
```

---

## 📸 Recommended Screenshots for Internship Report

1. **Resume Builder Dashboard**:
   - Showing GitHub username input (`octocat`), job description, template selector, and generated summary with project cards and PDF export options.
2. **Azure AI Analyzer Tab**:
   - The "Analyze & Match" view displaying the source selector toggle ("Use Resume Built in App" vs "Upload PDF/DOCX") and target job description.
3. **Document Upload & Validation**:
   - Drag-and-drop file upload zone displaying an uploaded `.pdf` or `.docx` resume with the 5 MB validation badge.
4. **Overall Match Gauge & Breakdown**:
   - The circular score gauge (with green/amber/rose dynamic color) alongside the 4 breakdown metrics (Skills, Keywords, Experience, Education).
5. **Skills Gap Analysis Chips**:
   - The matched skills chips (green badges) and missing skills chips (red badges) highlighting missing technical requirements.
6. **ATS Quality Audit & Recommendations**:
   - The section checklist, contact details check, word count, action verbs count, and the actionable AI improvement suggestions cards.
7. **FastAPI Swagger API Documentation (`/docs`)**:
   - Showing the interactive API endpoints: `/api/analyze-app-resume`, `/api/analyze-uploaded-resume`, and `/api/analyzer-status`.
8. **Unit Test Execution**:
   - Terminal screenshot displaying `python -m unittest discover -s tests` passing with `OK`.
