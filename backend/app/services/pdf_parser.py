import io
import pdfplumber
from fastapi import UploadFile, HTTPException



def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all readable text from a PDF's raw bytes.
    Returns an empty string if no text could be extracted.
    """
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def validate_and_extract_pdf(file: UploadFile) -> str:
    """
    Shared validation + extraction logic, used by every endpoint that accepts a PDF.
    Raises HTTPException directly so callers don't need to repeat error handling.
    """
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

    return extracted_text