import time
from groq import Groq, APIError

from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-20b"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def summarize_resume(resume_text: str, system_prompt: str) -> str:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": resume_text},
                ],
            )
            return response.choices[0].message.content
        except APIError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            continue

    raise RuntimeError(f"AI service error after {MAX_RETRIES} attempts: {last_error}")