from fastapi import FastAPI, UploadFile, File, HTTPException

from app.services.pdf_parser import extract_text_from_pdf
from app.models.schemas import ResumeUploadResponse

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