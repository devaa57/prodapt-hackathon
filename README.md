# AI Resume Screening Assistant

Multi-agent AI pipeline that screens candidates by comparing resumes against job descriptions.

## Architecture

```
POST /screen (resume_text + job_description)
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  Agent 1: Resume Analyzer      →  ResumeAnalysis    │
│  Agent 2: JD Analyzer          →  JobAnalysis       │
│  RAG: Chunk → Embed → Retrieve →  Evidence          │
│  Agent 3: Skill Matching       →  MatchingResult    │
│  Agent 4: Gap Analyzer         →  GapAnalysis       │
│  Scorer:  Deterministic Python →  CandidateScore    │
│  Agent 5: Report Generator     →  CandidateReport   │
└─────────────────────────────────────────────────────┘
       │
       ▼
  ScreeningResult (JSON)
```

All five "agents" use **one Gemini LLM** with specialised prompts and Pydantic structured outputs.

## Project Structure

```
app/
├── agents/            # Specialised LLM agents
│   ├── resume_agent   # Extracts structured resume data
│   ├── jd_agent       # Extracts structured JD requirements
│   ├── matching_agent # Classifies skill matches with evidence
│   ├── gap_agent      # Identifies gaps (NO_EVIDENCE, not "lacks")
│   └── report_agent   # Generates recruiter-friendly report
├── services/
│   ├── llm_service    # Centralised Gemini client + retry logic
│   ├── embedding_service  # text-embedding-004 wrapper
│   └── retrieval_service  # Chunking + in-memory vector search
├── schemas/
│   └── models         # All Pydantic models
├── scoring/
│   └── scorer         # Deterministic scoring engine
├── pipeline.py        # End-to-end orchestration
└── main.py            # FastAPI application

tests/                 # Unit + integration tests
```

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
copy .env.example .env
# Edit .env and add your Gemini API key

# 4. Run the server
uvicorn app.main:app --reload --port 8000

# 5. Test text endpoint
curl -X POST http://localhost:8000/screen \
  -H "Content-Type: application/json" \
  -d '{"job_description": "...", "resume_text": "..."}'

# 6. Test PDF endpoint
curl -X POST http://localhost:8000/screen/upload \
  -F "resume_file=@/path/to/resume.pdf" \
  -F "job_description=Senior ML Engineer requiring Python..."
```

## Database & Persistence
This branch integrates the `database-security-scalability` schema.
If `DATABASE_URL` is configured and PostgreSQL is reachable, every screening result (including candidates, jobs, and extracted skills) is saved to the database. If the database is offline, the pipeline gracefully skips persistence and still returns the AI analysis.

## Scoring Formula

```
score = 0.40 × required_skill_score
      + 0.25 × experience_score
      + 0.15 × semantic_score
      + 0.10 × education_score
      + 0.10 × preferred_skill_score
```

Weights are configurable. The LLM never determines the final score.

## Key Design Decisions

- **NO_EVIDENCE ≠ lacks skill**: If a resume doesn't mention AWS, we report `NO_EVIDENCE`, not "candidate doesn't know AWS."
- **Deterministic scoring**: Python calculates the final score, not the LLM.
- **In-memory RAG**: Uses numpy cosine similarity as a pgvector-free fallback.
- **Single Gemini client**: All agents share one `LLMService` instance.
- **Schema validation**: Every LLM response is validated via Pydantic. Invalid JSON triggers a self-correcting retry.

## Running Tests

```bash
# Unit tests (no API key needed)
pytest tests/test_scorer.py tests/test_schemas.py tests/test_retrieval.py -v

# Full integration test (needs GEMINI_API_KEY)
pytest tests/test_api.py -v -s -k "strong_candidate" --no-header
```

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required) |