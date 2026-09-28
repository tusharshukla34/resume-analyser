import re

# Prefixes that add no skill meaning: "MS-Excel", "Microsoft Excel" -> "excel"
_VENDOR_PREFIX = re.compile(r"^(ms|microsoft) ")

# Spelling variants and short forms -> one canonical form.
# Keys must already be in normalized form (lowercase, no hyphens or dots).
SKILL_ALIASES = {
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "ai": "artificial intelligence",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "llms": "llm",
    "large language models": "llm",
    "powerbi": "power bi",
    "sklearn": "scikit learn",
    "postgres": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "node js": "nodejs",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "amazon web services": "aws",
    "k8s": "kubernetes",
    "eda": "exploratory data analysis",
}


def normalize_skill(skill: str) -> str:
    """Reduce a skill name to a canonical form so spelling variants compare equal."""
    s = skill.strip().lower()
    s = s.replace(".", "")               # "Node.js" -> "nodejs"
    s = re.sub(r"[-_/]", " ", s)         # "MS-Excel" -> "ms excel"
    s = re.sub(r"\s+", " ", s).strip()
    s = _VENDOR_PREFIX.sub("", s)        # "ms excel" -> "excel"
    return SKILL_ALIASES.get(s, s)


def calculate_match_score(resume_skills: list[str], required_skills: list[str]) -> dict:
    """
    Pure, deterministic skill matching. No LLM involved.
    Both sides are normalized before comparing. Returns the role's original
    skill names, in the role's order, with duplicates counted once.
    """
    resume_keys = {normalize_skill(s) for s in resume_skills}
    resume_keys.discard("")

    matched: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()

    for skill in required_skills:
        key = normalize_skill(skill)
        if not key or key in seen:
            continue
        seen.add(key)
        (matched if key in resume_keys else missing).append(skill.strip())

    total = len(matched) + len(missing)
    percentage = round(len(matched) / total * 100, 1) if total else 0.0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": percentage,
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