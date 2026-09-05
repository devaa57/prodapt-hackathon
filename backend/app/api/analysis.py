from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.schemas.job import JobDescriptionRequest   

from app.core.security import get_current_user
from app.services import (
    analyze_resume,
    parse_job_description,
    parse_resume,
)


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


# ============================================================
# PARSE RESUME
# ============================================================

@router.post("/parse-resume")
async def parse_resume_endpoint(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    """
    Upload a PDF/DOCX resume and extract its text.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    allowed_extensions = {".pdf", ".docx"}

    extension = "." + file.filename.lower().split(".")[-1]

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:
        extracted_text = parse_resume(
            file_bytes,
            file.filename,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse resume.",
        )

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the resume.",
        )

    return {
        "filename": file.filename,
        "uploaded_by": current_user,
        "text": extracted_text,
        "character_count": len(extracted_text),
    }


# ============================================================
# PARSE JOB DESCRIPTION
# ============================================================

@router.post("/parse-jd")
async def parse_job_description_endpoint(
    request: JobDescriptionRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Parse a job description using OpenRouter.
    """

    job_description = request.job_description

    if not job_description:
        raise HTTPException(
            status_code=400,
            detail="job_description is required.",
        )

    if len(job_description.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job description must contain at least 20 characters.",
        )

    try:
        requirements = await parse_job_description(
            job_description
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    return {
        "analyzed_by": current_user,
        "requirements": requirements,
    }


# ============================================================
# ANALYZE RESUME
# ============================================================

@router.post("/analyze")
async def analyze_resume_endpoint(
    resume_file: UploadFile = File(...),
    job_description: str = "",
    current_user: str = Depends(get_current_user),
):
    """
    Analyze a resume against a job description.

    The endpoint:
    1. Parses the resume.
    2. Parses the job description.
    3. Sends both to OpenRouter.
    4. Returns a structured candidate analysis.
    """

    # --------------------------------------------------------
    # Validate resume
    # --------------------------------------------------------

    if not resume_file.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume filename is required.",
        )

    allowed_extensions = {".pdf", ".docx"}

    extension = "." + resume_file.filename.lower().split(".")[-1]

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    resume_bytes = await resume_file.read()

    if not resume_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded resume is empty.",
        )

    # --------------------------------------------------------
    # Validate job description
    # --------------------------------------------------------

    if not job_description:
        raise HTTPException(
            status_code=400,
            detail="job_description is required.",
        )

    if len(job_description.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job description must contain at least 20 characters.",
        )

    # --------------------------------------------------------
    # Parse resume
    # --------------------------------------------------------

    try:
        resume_text = parse_resume(
            resume_bytes,
            resume_file.filename,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse resume.",
        )

    if not resume_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the resume.",
        )

    # --------------------------------------------------------
    # Parse job description
    # --------------------------------------------------------

    try:
        job_requirements = await parse_job_description(
            job_description
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse job description: {exc}",
        )

    # --------------------------------------------------------
    # Analyze resume against requirements
    # --------------------------------------------------------

    try:
        analysis = await analyze_resume(
            resume_text=resume_text,
            job_requirements=job_requirements,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to analyze resume: {exc}",
        )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "analyzed_by": current_user,
        "filename": resume_file.filename,
        "job_requirements": job_requirements,
        "analysis": analysis,
    }