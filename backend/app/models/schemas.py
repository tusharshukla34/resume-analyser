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