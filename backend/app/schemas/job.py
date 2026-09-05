from pydantic import BaseModel, Field


class JobDescriptionRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=20,
        description="The complete job description",
    )


class JobRequirements(BaseModel):
    job_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_years: float | None
    education: list[str]
    responsibilities: list[str]
    keywords: list[str]