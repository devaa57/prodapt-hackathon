import json
from io import BytesIO

import httpx
from docx import Document
from pypdf import PdfReader

from app.core.config import settings


# ============================================================
# RESUME PARSING
# ============================================================

def parse_resume(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a PDF or DOCX resume.
    """

    extension = filename.lower().split(".")[-1]

    if extension == "pdf":
        return _parse_pdf(file_bytes)

    if extension == "docx":
        return _parse_docx(file_bytes)

    raise ValueError(
        "Unsupported file format. Please upload a PDF or DOCX file."
    )


def _parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages).strip()


def _parse_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs).strip()


# ============================================================
# OPENROUTER HELPER
# ============================================================

async def _call_openrouter(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    Send a request to OpenRouter and return the model's text response.
    """

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "temperature": 0.1,
        "response_format": {
            "type": "json_object"
        },
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code != 200:
        raise ValueError(
            f"OpenRouter API error: {response.status_code} - "
            f"{response.text}"
        )

    try:
        data = response.json()
    except json.JSONDecodeError:
        raise ValueError("OpenRouter returned an invalid API response.")

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ValueError(
            "Invalid response received from OpenRouter."
        )

    if not content:
        raise ValueError(
            "OpenRouter returned an empty response."
        )

    return content


def _parse_json_response(content: str) -> dict:
    """
    Safely convert the LLM response into a Python dictionary.
    """

    content = content.strip()

    # Remove markdown code fences if the model returns them.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

        if content.lower().startswith("json"):
            content = content[4:].strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(
            "OpenRouter returned invalid JSON."
        )

    if not isinstance(result, dict):
        raise ValueError(
            "OpenRouter returned JSON in an unexpected format."
        )

    return result


# ============================================================
# JOB DESCRIPTION PARSING
# ============================================================

async def parse_job_description(job_description: str) -> dict:
    """
    Extract structured requirements from a job description.
    """

    system_prompt = """
You are an expert recruitment and job-description analysis system.

Your task is to analyze a job description and extract structured,
objective requirements.

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{
    "job_title": "string",
    "required_skills": ["string"],
    "preferred_skills": ["string"],
    "experience_years": number or null,
    "education": ["string"],
    "responsibilities": ["string"],
    "keywords": ["string"]
}

Rules:

1. required_skills must contain skills explicitly required by the job.
2. preferred_skills must contain skills described as preferred,
   nice-to-have, bonus, or equivalent.
3. Do not invent skills that are not supported by the job description.
4. If experience is not specified, use null.
5. If a range is given, extract the minimum required years.
6. Keep skill names concise and standardized.
7. Do not include explanations outside the JSON.
"""

    user_prompt = f"""
Analyze this job description:

--- JOB DESCRIPTION ---

{job_description}

--- END JOB DESCRIPTION ---
"""

    content = await _call_openrouter(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return _parse_json_response(content)


# ============================================================
# RESUME VS JOB ANALYSIS
# ============================================================

async def analyze_resume(
    resume_text: str,
    job_requirements: dict,
) -> dict:
    """
    Compare a resume against structured job requirements
    using OpenRouter.
    """

    system_prompt = """
You are an expert AI recruitment screening system.

Your task is to objectively compare a candidate's resume
against a job's requirements.

You must NOT invent candidate experience, skills,
education, certifications, or achievements.

Only use information explicitly present in the resume.

Return ONLY valid JSON.

Use exactly this structure:

{
    "overall_score": 0,
    "recommendation": "Strong Match",
    "summary": "string",
    "matched_required_skills": [
        "string"
    ],
    "missing_required_skills": [
        "string"
    ],
    "matched_preferred_skills": [
        "string"
    ],
    "experience_match": {
        "required_years": 0,
        "candidate_years": 0,
        "meets_requirement": true
    },
    "education_match": true,
    "strengths": [
        "string"
    ],
    "gaps": [
        "string"
    ]
}

Rules:

1. overall_score must be an integer from 0 to 100.
2. Score based primarily on required skills and experience.
3. Required skills are more important than preferred skills.
4. Do not give credit for skills that are not present in the resume.
5. Do not assume that similar technologies are identical unless
   there is reasonable evidence in the resume.
6. If experience_years is null, do not penalize the candidate
   for missing experience information.
7. If education requirements are empty, set education_match to true.
8. recommendation must be one of:
   - "Strong Match"
   - "Good Match"
   - "Partial Match"
   - "Not a Match"
9. Be objective and concise.
10. Do not include explanations outside the JSON.
"""

    user_prompt = f"""
Compare the following candidate resume against the job requirements.

================ RESUME ================

{resume_text}

================ JOB REQUIREMENTS ================

{json.dumps(job_requirements, indent=2)}

================ END INPUT ================

Return the recruitment analysis as JSON.
"""

    content = await _call_openrouter(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return _parse_json_response(content)