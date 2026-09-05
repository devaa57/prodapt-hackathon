from pydantic import BaseModel


class SkillEvidence(BaseModel):
    skill: str
    matched: bool
    evidence: str


class ExperienceMatch(BaseModel):
    required_years: float | None
    candidate_years: float | None
    matched: bool
    evidence: str


class EducationMatch(BaseModel):
    required_education: list[str]
    candidate_education: str
    matched: bool
    evidence: str


class CandidateAnalysis(BaseModel):
    matched_required_skills: list[SkillEvidence]
    missing_required_skills: list[str]
    matched_preferred_skills: list[SkillEvidence]
    experience_match: ExperienceMatch
    education_match: EducationMatch
    relevant_experience: list[str]
    candidate_summary: str