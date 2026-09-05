"""
FastAPI application — entry point for the AI Resume Screening Assistant.

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline import ScreeningPipeline
from app.schemas.models import ScreeningRequest, ScreeningResult
from app.db.connection import db_pool
from app.db.repository import ScreeningRepository
from app.services.pdf_service import PDFService

# Load .env before anything touches os.getenv
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── FastAPI app ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database pool...")
    db_pool.initialize()
    yield
    # Shutdown
    logger.info("Closing database pool...")
    db_pool.close()

app = FastAPI(
    title="AI Resume Screening Assistant",
    description=(
        "Multi-agent pipeline that analyses resumes against job descriptions, "
        "performs RAG-based evidence retrieval, deterministic scoring, "
        "and generates recruiter-friendly reports."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy pipeline singleton ───────────────────────────────────────

_pipeline: ScreeningPipeline | None = None


def _get_pipeline() -> ScreeningPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ScreeningPipeline()
    return _pipeline


# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}


@app.post(
    "/screen",
    response_model=ScreeningResult,
    tags=["screening"],
    summary="Screen a candidate (Text)",
    description=(
        "Accepts raw resume text and a job description. "
        "Returns structured analysis, skill matches, gap analysis, "
        "a deterministic score, and a recruiter report."
    ),
)
def screen_candidate(request: ScreeningRequest) -> ScreeningResult:
    """Run the full screening pipeline on raw text."""
    if not request.resume_text.strip():
        raise HTTPException(status_code=422, detail="resume_text must not be empty.")
    if not request.job_description.strip():
        raise HTTPException(status_code=422, detail="job_description must not be empty.")

    try:
        pipeline = _get_pipeline()
        result = pipeline.screen(
            resume_text=request.resume_text,
            job_description=request.job_description,
        )
        # Persist to database
        repo = ScreeningRepository(db_pool)
        sid = repo.persist_screening(
            result, 
            resume_text=request.resume_text, 
            job_description=request.job_description
        )
        if sid:
            result.screening_id = sid
        return result
    except ValueError as exc:
        logger.error("Pipeline validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Pipeline failed unexpectedly")
        raise HTTPException(status_code=500, detail=f"Screening failed: {exc}")


@app.post(
    "/screen/upload",
    response_model=ScreeningResult,
    tags=["screening"],
    summary="Screen a candidate (PDF Upload)",
    description=(
        "Upload a PDF resume and provide a job description string. "
        "Extracts text with page awareness before screening."
    ),
)
async def screen_candidate_pdf(
    resume_file: UploadFile = File(..., description="PDF resume file"),
    job_description: str = Form(..., description="Raw job description text"),
) -> ScreeningResult:
    """Run the pipeline on an uploaded PDF resume."""
    if not resume_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="job_description must not be empty.")

    try:
        file_bytes = await resume_file.read()
        pages = PDFService.extract_pages(file_bytes)
        
        pipeline = _get_pipeline()
        result = pipeline.screen(
            job_description=job_description,
            pages=pages,
        )
        
        # Persist to database
        repo = ScreeningRepository(db_pool)
        sid = repo.persist_screening(
            result, 
            resume_text=PDFService.pages_to_text(pages),
            job_description=job_description
        )
        if sid:
            result.screening_id = sid
        return result
        
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Pipeline failed unexpectedly")
        raise HTTPException(status_code=500, detail=f"Screening failed: {exc}")
