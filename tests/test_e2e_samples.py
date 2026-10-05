import os
import sys

# Ensure app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.azure_analyzer import AzureResumeAnalyzer

def run_test():
    analyzer = AzureResumeAnalyzer()
    
    # 1. Test DOCX
    docx_path = os.path.join(os.path.dirname(__file__), "..", "sample_resumes", "sample_software_engineer_resume.docx")
    with open(docx_path, "rb") as f:
        docx_bytes = f.read()
    text_docx, method_docx = analyzer.extract_text_from_file(docx_bytes, "sample.docx")
    print(f"[OK] DOCX Extraction ({method_docx}): {len(text_docx)} chars extracted")
    assert len(text_docx) > 50

    # 2. Test PDF
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_resumes", "sample_software_engineer_resume.pdf")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    text_pdf, method_pdf = analyzer.extract_text_from_file(pdf_bytes, "sample.pdf")
    print(f"[OK] PDF Extraction ({method_pdf}): {len(text_pdf)} chars extracted")
    assert len(text_pdf) > 50

    # 3. Test Full Analysis
    job_desc = "We are seeking a Senior Python Developer with strong expertise in FastAPI, Docker, and Microsoft Azure."
    result = analyzer.analyze_resume_against_job(text_docx, job_desc, extraction_method=method_docx)
    
    print("\n" + "="*50)
    print("ANALYSIS RESULT VERIFICATION:")
    print("="*50)
    print(f"Overall Score: {result['overall_score']}%")
    print(f"Matched Skills: {result['matched_skills']}")
    print(f"Missing Skills: {result['missing_skills']}")
    print(f"Score Breakdown: {result['score_breakdown']}")
    print(f"Quality Rating: {result['quality_report']['overall_quality']}")
    print(f"Suggestions Count: {len(result['quality_report']['suggestions'])}")
    print("="*50)
    
    assert 0 <= result['overall_score'] <= 100
    assert len(result['matched_skills']) > 0
    print("[OK] All end-to-end sample tests passed successfully!")

if __name__ == "__main__":
    run_test()
