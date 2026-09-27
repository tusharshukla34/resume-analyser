def calculate_match_score(resume_skills: list[str], required_skills: list[str]) -> dict:
    """
    Pure, deterministic skill matching. No LLM involved.
    Case-insensitive comparison so "python" matches "Python".
    """
    resume_set = {s.strip().lower() for s in resume_skills}
    required_set = {s.strip().lower() for s in required_skills}

    matched = required_set & resume_set
    missing = required_set - resume_set

    percentage = (len(matched) / len(required_set) * 100) if required_set else 0.0

    return {
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "match_percentage": round(percentage, 1),
    }


# Tool schema describing this function to the LLM
MATCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_match_score",
        "description": "Calculates exact matched skills, missing skills, and match percentage between a resume and a role's required skills.",
        "parameters": {
            "type": "object",
            "properties": {
                "resume_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills found in the candidate's resume.",
                },
                "required_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills required for the job role.",
                },
            },
            "required": ["resume_skills", "required_skills"],
        },
    },
}