from pydantic import BaseModel

from typing import List

class ResumeUploadResponse(BaseModel):
    filename: str
    extracted_text: str
    character_count: int
class ResumeStructured(BaseModel):
    candidate_summary: str
    skills: List[str]
    education: List[str]
    experience: List[str]
    projects: List[str]
class RoleRequest(BaseModel):
    role_title: str
class RoleRequirements(BaseModel):
    role_title: str
    required_skills: List[str]
    keywords: List[str]
    typical_responsibilities: List[str]      
class MatchRequest(BaseModel):
    resume: ResumeStructured
    role: RoleRequirements
class MatchResult(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    match_percentage: float
    analysis: str      