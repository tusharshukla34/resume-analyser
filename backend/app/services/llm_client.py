import time
from groq import Groq, APIError

from app.config import GROQ_API_KEY


from app.models.schemas import RoleRequirements

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


from app.models.schemas import ResumeStructured


def extract_structured_resume(resume_text: str, system_prompt: str) -> ResumeStructured:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": resume_text},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "resume_structured",
                        "schema": ResumeStructured.model_json_schema(),
                    },
                },
            )
            raw_json = response.choices[0].message.content
            return ResumeStructured.model_validate_json(raw_json)

        except APIError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            continue
        except ValueError as e:  # Pydantic validation errors subclass ValueError
            last_error = e
            break  # don't retry on a schema mismatch, likely a persistent issue

    raise RuntimeError(f"Failed to extract structured resume data: {last_error}")


def get_role_requirements(role_title: str, system_prompt: str) -> RoleRequirements:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Job role: {role_title}"},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "role_requirements",
                        "schema": RoleRequirements.model_json_schema(),
                    },
                },
            )
            raw_json = response.choices[0].message.content
            return RoleRequirements.model_validate_json(raw_json)

        except APIError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            continue
        except ValueError as e:
            last_error = e
            break

    raise RuntimeError(f"Failed to get role requirements: {last_error}")