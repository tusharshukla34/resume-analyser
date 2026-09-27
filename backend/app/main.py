from fastapi import FastAPI, UploadFile, File, HTTPException

from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm_client import (
    summarize_resume,
    extract_structured_resume,
    get_role_requirements,
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
)




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