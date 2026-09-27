import io
import pdfplumber


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