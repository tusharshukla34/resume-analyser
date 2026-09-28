import sys
from pathlib import Path

from app.services.llm_client import extract_structured_resume, get_role_requirements
from app.services.matcher import calculate_match_score, normalize_skill
from app.prompts.resume_prompts import RESUME_EXTRACTION_SYSTEM_PROMPT
from app.prompts.role_prompts import ROLE_UNDERSTANDING_SYSTEM_PROMPT

FIXTURE = Path(__file__).parent / "fixtures" / "sample_resume.txt"

# Skills the sample resume clearly shows. If the role requires one of these
# and the matcher reports it missing, that is a "false gap".
CLEARLY_PRESENT = {"python", "sql", "tableau", "power bi", "excel"}


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    role = sys.argv[2] if len(sys.argv) > 2 else "Data Analyst"
    resume_text = FIXTURE.read_text(encoding="utf-8")

    scores = []
    required_per_run = []
    total_false_gaps = 0

    for i in range(1, runs + 1):
        resume = extract_structured_resume(resume_text, RESUME_EXTRACTION_SYSTEM_PROMPT)
        role_data = get_role_requirements(role, ROLE_UNDERSTANDING_SYSTEM_PROMPT)
        result = calculate_match_score(resume.skills, role_data.required_skills)

        required = {normalize_skill(s) for s in role_data.required_skills}
        false_gaps = {normalize_skill(s) for s in result["missing_skills"]} & CLEARLY_PRESENT
        
        scores.append(result["match_percentage"])
        required_per_run.append(required)
        total_false_gaps += len(false_gaps)

        print(
            f"run {i}: score={result['match_percentage']}%  "
            f"required={len(required)}  resume_skills={len(resume.skills)}  "
            f"false_gaps={sorted(false_gaps) or '-'}"
        )

    always = set.intersection(*required_per_run)
    sometimes = set.union(*required_per_run) - always

    print("\n--- summary ---")
    print(f"scores: {scores}")
    print(f"spread: {max(scores) - min(scores):.1f} points (min {min(scores)}, max {max(scores)})")
    print(f"role skills in every run: {sorted(always)}")
    print(f"role skills that came and went: {sorted(sometimes)}")
    print(f"false gaps across all runs: {total_false_gaps}")


if __name__ == "__main__":
    main()