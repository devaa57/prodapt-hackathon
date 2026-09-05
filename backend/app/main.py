from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.analysis import router as analysis_router


app = FastAPI(
    title="AI Resume Screening Assistant",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(auth_router)
app.include_router(analysis_router)