import os
import json
import openai
from app.schemas import JobSkills

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_skills_from_job_description(job_description: str) -> JobSkills:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
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
            {
                "role": "user",
                "content": job_description
            }
        ]
    )

    content = response.output_text
    data = json.loads(content)

    return JobSkills(**data)