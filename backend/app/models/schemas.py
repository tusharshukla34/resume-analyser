from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    filename: str
    extracted_text: str
    character_count: int


from typing import List


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