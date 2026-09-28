import sys
from collections import Counter

from app.services.llm_client import get_role_requirements
from app.services.matcher import calculate_match_score, normalize_skill
from app.prompts.role_prompts import ROLE_UNDERSTANDING_SYSTEM_PROMPT

# Fixed resume skills, so only the role step can change the score.
FIXED_RESUME_SKILLS = [
    "Python", "SQL", "MySQL", "Machine Learning",
    "Tableau", "Power BI", "MS-Excel", "Azure",
]


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    role = sys.argv[2] if len(sys.argv) > 2 else "Data Analyst"

    lists = []
    scores = []

    for i in range(1, runs + 1):
        data = get_role_requirements(role, ROLE_UNDERSTANDING_SYSTEM_PROMPT)
        keys = tuple(sorted({normalize_skill(s) for s in data.required_skills} - {""}))
        score = calculate_match_score(FIXED_RESUME_SKILLS, data.required_skills)["match_percentage"]
        lists.append(keys)
        scores.append(score)
        print(f"run {i}: required={len(keys)}  score={score}%")

    counts = Counter(skill for keys in lists for skill in keys)
    always = sorted(s for s, c in counts.items() if c == runs)
    sometimes = sorted(
        ((s, c) for s, c in counts.items() if c < runs), key=lambda item: -item[1]
    )

    print("\n--- summary ---")
    print(f"distinct skill lists: {len(set(lists))} of {runs} runs")
    print(f"list lengths: {dict(sorted(Counter(len(k) for k in lists).items()))}")
    print(f"score spread: {max(scores) - min(scores):.1f} points (min {min(scores)}, max {max(scores)})")
    print(f"in every run ({len(always)}): {always}")
    print("in some runs: " + (", ".join(f"{s} ({c}/{runs})" for s, c in sometimes) or "none"))


if __name__ == "__main__":
    main()