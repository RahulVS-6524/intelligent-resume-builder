import os
import json
import re
from app.schemas import JobSkills

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def extract_skills_from_job_description(job_description: str) -> JobSkills:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if OPENAI_AVAILABLE and api_key and not api_key.startswith("your_"):
        try:
            client = openai.OpenAI(api_key=api_key)
            # Try chat completions or responses API
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a resume parser. "
                                "Return ONLY valid JSON in this format:\n"
                                "{\n"
                                "  \"required_skills\": [\"skill1\", \"skill2\"],\n"
                                "  \"preferred_skills\": [\"skillA\", \"skillB\"]\n"
                                "}"
                            )
                        },
                        {"role": "user", "content": job_description}
                    ]
                )
                content = response.choices[0].message.content.strip()
            except Exception:
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {
                            "role": "system",
                            "content": "You are a resume parser. Return ONLY valid JSON: {\"required_skills\": [...], \"preferred_skills\": [...]}"
                        },
                        {"role": "user", "content": job_description}
                    ]
                )
                content = response.output_text.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return JobSkills(**data)
        except Exception as e:
            print(f"OpenAI error: {e}. Using fallback skill extraction.")

    # Graceful NLP/regex fallback
    tech_keywords = [
        "python", "javascript", "typescript", "react", "fastapi", "docker", "kubernetes",
        "aws", "azure", "postgresql", "sql", "git", "linux", "rest", "machine learning",
        "django", "flask", "node.js", "mongodb", "ci/cd", "html", "css"
    ]
    words = job_description.lower()
    matched = [k.title() for k in tech_keywords if re.search(r'(?<![a-zA-Z0-9#+])' + re.escape(k) + r'(?![a-zA-Z0-9#+])', words)]
    return JobSkills(
        required_skills=matched[:4],
        preferred_skills=matched[4:8]
    )