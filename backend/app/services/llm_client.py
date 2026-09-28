import time
from groq import Groq, APIError
from app.config import GROQ_API_KEY
import json
from app.services.matcher import calculate_match_score, MATCH_TOOL_SCHEMA
from app.models.schemas import RoleRequirements

client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-20b"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def call_llm_with_retry(create_request_fn, parse_response_fn):
    """
    Shared retry-with-backoff wrapper for any LLM call.
    create_request_fn: a zero-arg function that performs the actual API call and returns the raw response.
    parse_response_fn: a function that takes the raw response and returns the final parsed result
                        (may raise ValueError/ValidationError for non-retryable failures).
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw_response = create_request_fn()
            return parse_response_fn(raw_response)
        except APIError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            continue
        except ValueError as e:
            last_error = e
            break

    raise RuntimeError(f"LLM call failed after retries: {last_error}")

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
                temperature=0,
                seed=42,    
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



def generate_match_analysis(resume_skills: list[str], required_skills: list[str], system_prompt: str) -> str:
    """
    Uses tool calling: the LLM calls calculate_match_score to get real numbers,
    then writes an analysis grounded in that result.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Resume skills: {resume_skills}\nRequired skills: {required_skills}",
        },
    ]

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Turn 1: let the LLM decide to call the tool
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                max_tokens=500,
                messages=messages,
                tools=[MATCH_TOOL_SCHEMA],
                tool_choice="auto",
            )
            message = response.choices[0].message

            if not message.tool_calls:
                # LLM answered directly without calling the tool - unusual, but handle gracefully
                return message.content

            # Execute the real tool call ourselves
            tool_call = message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            tool_result = calculate_match_score(**args)

            # Feed the tool result back to the LLM
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result),
            })

            # Turn 2: get the final, grounded analysis
            final_response = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                max_tokens=500,
                messages=messages,
            )
            return final_response.choices[0].message.content

        except APIError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            continue

    raise RuntimeError(f"Failed to generate match analysis: {last_error}")

from app.models.schemas import SuggestionResult


def generate_suggestions(
    role_title: str,
    matched_skills: list[str],
    missing_skills: list[str],
    system_prompt: str,
) -> SuggestionResult:
    user_content = (
        f"Job role: {role_title}\n"
        f"Matched skills: {matched_skills}\n"
        f"Missing skills: {missing_skills}"
    )

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.3,
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "suggestion_result",
                        "schema": SuggestionResult.model_json_schema(),
                    },
                },
            )
            raw_json = response.choices[0].message.content
            return SuggestionResult.model_validate_json(raw_json)

        except APIError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            continue
        except ValueError as e:
            last_error = e
            break

    raise RuntimeError(f"Failed to generate suggestions: {last_error}")