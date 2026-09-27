from app.services.llm_client import (
    extract_structured_resume,
    get_role_requirements,
    generate_match_analysis,
    generate_suggestions,
)
from app.services.matcher import calculate_match_score
from app.prompts.resume_prompts import RESUME_EXTRACTION_SYSTEM_PROMPT
from app.prompts.role_prompts import ROLE_UNDERSTANDING_SYSTEM_PROMPT
from app.prompts.match_prompts import MATCH_ANALYSIS_SYSTEM_PROMPT
from app.prompts.suggestion_prompts import SUGGESTION_SYSTEM_PROMPT
from app.models.schemas import FullAnalysisResult, Suggestion


def run_resume_analysis_pipeline(resume_text: str, role_title: str) -> FullAnalysisResult:
    # Step 1: understand the resume
    resume_data = extract_structured_resume(resume_text, RESUME_EXTRACTION_SYSTEM_PROMPT)

    # Step 2: understand the role
    role_data = get_role_requirements(role_title, ROLE_UNDERSTANDING_SYSTEM_PROMPT)

    # Step 3: deterministic matching (our own trusted numbers)
    score_data = calculate_match_score(resume_data.skills, role_data.required_skills)

    # Step 4: grounded match analysis (tool calling)
    match_analysis = generate_match_analysis(
        resume_data.skills, role_data.required_skills, MATCH_ANALYSIS_SYSTEM_PROMPT
    )

    # Step 5: suggestions (skip LLM call if no gaps)
    if score_data["missing_skills"]:
        suggestion_result = generate_suggestions(
            role_title, score_data["matched_skills"], score_data["missing_skills"], SUGGESTION_SYSTEM_PROMPT
        )
        suggestions = suggestion_result.suggestions
        overall_advice = suggestion_result.overall_advice
    else:
        suggestions = []
        overall_advice = (
            f"Great news — your resume already covers all the key skills "
            f"typically required for a {role_title} role. "
            f"Focus on quantifying your impact in existing experience and projects."
        )

    return FullAnalysisResult(
        resume=resume_data,
        role=role_data,
        matched_skills=score_data["matched_skills"],
        missing_skills=score_data["missing_skills"],
        match_percentage=score_data["match_percentage"],
        match_analysis=match_analysis,
        suggestions=suggestions,
        overall_advice=overall_advice,
    )