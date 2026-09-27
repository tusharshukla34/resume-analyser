from fastapi import FastAPI, UploadFile, File, HTTPException

from app.services.pdf_parser import extract_text_from_pdf
from app.services.matcher import calculate_match_score

from app.prompts.match_prompts import MATCH_ANALYSIS_SYSTEM_PROMPT
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
from app.models.schemas import (
    ResumeUploadResponse,
    ResumeStructured,
    RoleRequest,
    RoleRequirements,
    MatchRequest,
    MatchResult,
    SuggestionRequest,
    SuggestionResult,
)

from app.prompts.suggestion_prompts import SUGGESTION_SYSTEM_PROMPT

app = FastAPI(title="Resume Analyzer API")

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "resume-analyzer-backend"}


@app.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    # 1. Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 2. Read bytes and validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5MB size limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 3. Extract text
    try:
        extracted_text = extract_text_from_pdf(contents)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this PDF. It may be corrupted.")

    # 4. Validate extraction result
    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted. The PDF may be scanned/image-based.",
        )

    return ResumeUploadResponse(
        filename=file.filename,
        extracted_text=extracted_text,
        character_count=len(extracted_text),
    )


@app.post("/summarize-resume")
async def summarize_resume_endpoint(file: UploadFile = File(...)):
    # Reuse Phase 2 validation + extraction
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5MB size limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        extracted_text = extract_text_from_pdf(contents)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this PDF. It may be corrupted.")

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted.")

    # NEW: call the LLM
    try:
        summary = summarize_resume(extracted_text, RESUME_SUMMARY_SYSTEM_PROMPT)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"filename": file.filename, "summary": summary}



@app.post("/analyze-resume", response_model=ResumeStructured)
async def analyze_resume_endpoint(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5MB size limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        extracted_text = extract_text_from_pdf(contents)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read this PDF. It may be corrupted.")

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted.")

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

    # Our own trusted calculation - always the source of truth for numbers returned to the client
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
    # Handle the "no gaps" case without spending an LLM call
    if not payload.missing_skills:
        return SuggestionResult(
            suggestions=[],
            overall_advice=(
                f"Great news — your resume already covers all the key skills "
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