from app.services.matcher import calculate_match_score

# (name, resume_skills, required_skills, expected_matched, expected_missing)
CASES = [
    ("vendor prefix", ["MS-Excel"], ["Excel"], ["Excel"], []),
    ("microsoft prefix", ["Microsoft Excel"], ["Excel"], ["Excel"], []),
    ("casing", ["python"], ["Python"], ["Python"], []),
    ("hyphen vs space", ["Scikit-learn"], ["scikit learn"], ["scikit learn"], []),
    ("abbreviation ML", ["ML"], ["Machine Learning"], ["Machine Learning"], []),
    ("abbreviation JS", ["JS"], ["JavaScript"], ["JavaScript"], []),
    ("dot variants", ["Node.js"], ["Node JS"], ["Node JS"], []),
    ("duplicates counted once", ["SQL"], ["SQL", "sql"], ["SQL"], []),
    ("empty required list", ["Python"], [], [], []),
    ("must NOT match: Java vs JavaScript", ["Java"], ["JavaScript"], [], ["JavaScript"]),
    ("must NOT match: R vs React", ["R"], ["React"], [], ["React"]),
    ("known limitation: MySQL vs SQL", ["MySQL"], ["SQL"], [], ["SQL"]),
]


def main() -> None:
    failed = 0
    for name, resume, required, exp_matched, exp_missing in CASES:
        result = calculate_match_score(resume, required)
        ok = result["matched_skills"] == exp_matched and result["missing_skills"] == exp_missing
        failed += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"      got matched={result['matched_skills']} missing={result['missing_skills']}")

    score = calculate_match_score(["Python", "SQL"], ["Python", "SQL", "Excel", "R"])["match_percentage"]
    score_ok = score == 50.0
    failed += 0 if score_ok else 1
    print(f"{'PASS' if score_ok else 'FAIL'}  score: 2 of 4 required is 50.0 (got {score})")

    print(f"\n{len(CASES) + 1 - failed} of {len(CASES) + 1} checks passed")


if __name__ == "__main__":
    main()