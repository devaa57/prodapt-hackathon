# HireLens · AI Resume Screening Assistant

Professional recruiter workspace for requirement-document parsing, resume ingest, and ranked candidate screening.

## Stack

- **Frontend:** React, Vite, TypeScript, Tailwind (`frontend/`)
- **Backend APIs:** FastAPI, SQLite, JWT (`backend/`)

## Run locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to the FastAPI server.

## Product flow

1. Register / sign in
2. Create a role
3. Upload a requirement document (PDF, DOCX, TXT)
4. Bulk-upload candidate resumes
5. Run AI screening and shortlist or reject from ranked results

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create recruiter |
| POST | `/api/auth/login` | JWT login |
| GET | `/api/auth/me` | Current user |
| GET | `/api/dashboard` | KPIs and score buckets |
| GET/POST | `/api/jobs` | List / create roles |
| GET/PATCH/DELETE | `/api/jobs/{id}` | Role detail |
| POST | `/api/jobs/{id}/requirement` | Upload JD |
| GET/POST | `/api/jobs/{id}/candidates` | List / upload resumes |
| POST | `/api/jobs/{id}/screen` | Rank candidates |
| GET | `/api/jobs/{id}/results` | Ranked results |
| GET/PATCH/DELETE | `/api/candidates/{id}` | Dossier and status |
