import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.azure_analyzer import AzureResumeAnalyzer

def run_benchmarks():
    analyzer = AzureResumeAnalyzer()
    
    docx_path = os.path.join(os.path.dirname(__file__), "..", "sample_resumes", "sample_software_engineer_resume.docx")
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_resumes", "sample_software_engineer_resume.pdf")

    with open(docx_path, "rb") as f:
        docx_bytes = f.read()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    job_desc = (
        "Seeking a Senior Python Developer with 4+ years of experience in FastAPI, Docker, "
        "Kubernetes, and Microsoft Azure cloud infrastructure. Hands-on database optimization "
        "with PostgreSQL and CI/CD automation."
    )

    # 1. Benchmark DOCX extraction
    t0 = time.perf_counter()
    text_docx, method_docx = analyzer.extract_text_from_file(docx_bytes, "sample.docx")
    t_docx = (time.perf_counter() - t0) * 1000

    # 2. Benchmark PDF extraction
    t0 = time.perf_counter()
    text_pdf, method_pdf = analyzer.extract_text_from_file(pdf_bytes, "sample.pdf")
    t_pdf = (time.perf_counter() - t0) * 1000

    # 3. Benchmark Entity & Key Phrase Extraction
    t0 = time.perf_counter()
    entities, method_nlp = analyzer.extract_entities_and_phrases(text_docx)
    t_nlp = (time.perf_counter() - t0) * 1000

    # 4. Benchmark Matching & Scoring Algorithm
    t0 = time.perf_counter()
    score, breakdown, matched, missing = analyzer.calculate_match_score(
        resume_text=text_docx,
        resume_entities=entities,
        job_text=job_desc,
        job_entities=analyzer.extract_entities_and_phrases(job_desc)[0]
    )
    t_scoring = (time.perf_counter() - t0) * 1000

    # 5. Benchmark Quality Audit
    t0 = time.perf_counter()
    quality = analyzer.check_resume_quality(text_docx, entities, missing)
    t_quality = (time.perf_counter() - t0) * 1000

    # 6. Full End-to-End Pipeline
    t0 = time.perf_counter()
    full_res = analyzer.analyze_resume_against_job(text_docx, job_desc, extraction_method="benchmark")
    t_e2e = (time.perf_counter() - t0) * 1000

    print("--- BENCHMARK RESULTS ---")
    print(f"DOCX Extraction: {t_docx:.2f} ms")
    print(f"PDF Extraction: {t_pdf:.2f} ms")
    print(f"Entity & Phrase Extraction: {t_nlp:.2f} ms")
    print(f"Scoring Calculation: {t_scoring:.2f} ms")
    print(f"Quality Audit: {t_quality:.2f} ms")
    print(f"Total Pipeline Latency: {t_e2e:.2f} ms")
    print(f"Score: {score}%, Matched Skills: {len(matched)}, Missing: {len(missing)}")

if __name__ == "__main__":
    run_benchmarks()
