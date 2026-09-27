import logging
import time

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS, GROQ_API_KEY
from app.services.pdf_parser import validate_and_extract_pdf
from app.services.matcher import calculate_match_score
from app.services.pipeline import run_resume_analysis_pipeline
from app.services.llm_client import (
    summarize_resume,
    extract_structured_resume,
    get_role_requirements,
    generate_match_analysis,
    generate_suggestions,
)
from app.prompts.resume_prompts import (
    RESUME_SUMMARY_SYSTEM_PROMPT,
    RESUME_EXTRACTION_SYSTEM_PROMPT,
)
from app.prompts.role_prompts import ROLE_UNDERSTANDING_SYSTEM_PROMPT
from app.prompts.match_prompts import MATCH_ANALYSIS_SYSTEM_PROMPT
from app.prompts.suggestion_prompts import SUGGESTION_SYSTEM_PROMPT
from app.models.schemas import (
    ResumeUploadResponse,
    ResumeStructured,
    RoleRequest,
    RoleRequirements,
    MatchRequest,
    MatchResult,
    SuggestionRequest,
    SuggestionResult,
    FullAnalysisResult,
)

app = FastAPI(title="Resume Analyzer API")

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("resume_analyzer")

# --- CORS setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request logging middleware ---
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    logger.info(f"Request started: {request.method} {request.url.path}")

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"Request completed: {request.method} {request.url.path} "
        f"- status={response.status_code} - {duration:.2f}s"
    )
    return response


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "resume-analyzer-backend",
        "groq_api_configured": bool(GROQ_API_KEY),
    }


@app.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    extracted_text = await validate_and_extract_pdf(file)
    return ResumeUploadResponse(
        filename=file.filename,
        extracted_text=extracted_text,
        character_count=len(extracted_text),
    )


@app.post("/summarize-resume")
async def summarize_resume_endpoint(file: UploadFile = File(...)):
    extracted_text = await validate_and_extract_pdf(file)
    try:
        summary = summarize_resume(extracted_text, RESUME_SUMMARY_SYSTEM_PROMPT)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"filename": file.filename, "summary": summary}


@app.post("/analyze-resume", response_model=ResumeStructured)
async def analyze_resume_endpoint(file: UploadFile = File(...)):
    extracted_text = await validate_and_extract_pdf(file)
    try:
        structured_data = extract_structured_resume(extracted_text, RESUME_EXTRACTION_SYSTEM_PROMPT)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return structured_data


@app.post("/understand-role", response_model=RoleRequirements)
async def understand_role_endpoint(payload: RoleRequest):
    role_title = payload.role_title.strip()
    if not role_title:
        raise HTTPException(status_code=400, detail="Role title cannot be empty.")
    if len(role_title) > 100:
        raise HTTPException(status_code=400, detail="Role title is too long.")
    try:
        role_data = get_role_requirements(role_title, ROLE_UNDERSTANDING_SYSTEM_PROMPT)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return role_data


@app.post("/match-resume-to-role", response_model=MatchResult)
async def match_resume_to_role_endpoint(payload: MatchRequest):
    resume_skills = payload.resume.skills
    required_skills = payload.role.required_skills
    score_data = calculate_match_score(resume_skills, required_skills)
    try:
        analysis = generate_match_analysis(resume_skills, required_skills, MATCH_ANALYSIS_SYSTEM_PROMPT)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return MatchResult(
        matched_skills=score_data["matched_skills"],
        missing_skills=score_data["missing_skills"],
        match_percentage=score_data["match_percentage"],
        analysis=analysis,
    )


@app.post("/generate-suggestions", response_model=SuggestionResult)
async def generate_suggestions_endpoint(payload: SuggestionRequest):
    if not payload.missing_skills:
        return SuggestionResult(
            suggestions=[],
            overall_advice=(
                f"Great news - your resume already covers all the key skills "
                f"typically required for a {payload.role_title} role. "
                f"Focus on quantifying your impact in existing experience and projects."
            ),
        )
    try:
        result = generate_suggestions(
            payload.role_title,
            payload.matched_skills,
            payload.missing_skills,
            SUGGESTION_SYSTEM_PROMPT,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return result


@app.post("/full-analysis", response_model=FullAnalysisResult)
async def full_analysis_endpoint(file: UploadFile = File(...), role_title: str = Form(...)):
    role_title = role_title.strip()
    if not role_title:
        raise HTTPException(status_code=400, detail="Role title cannot be empty.")
    if len(role_title) > 100:
        raise HTTPException(status_code=400, detail="Role title is too long.")

    extracted_text = await validate_and_extract_pdf(file)

    try:
        result = run_resume_analysis_pipeline(extracted_text, role_title)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return result