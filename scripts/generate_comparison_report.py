"""
Produces the GenAI-vs-Python Comparison Report deliverable (SRS requires
100+ cases). Uses the SIMULATED GenAI client by default so this can run
without API costs — pass --live to use the real Anthropic client instead
(requires ANTHROPIC_API_KEY in .env and will cost money / take longer).

Run: python scripts/generate_comparison_report.py
     python scripts/generate_comparison_report.py --live --limit 50
"""
import argparse
import csv
import random
from pathlib import Path

from comparison_engine.comparator import build_comparison_row
from database.models import Complaint
from database.session import SessionLocal, init_db
from genai_pipeline.simulate import simulate_analysis
from python_validation.pipeline import validate_analysis
from python_validation.rule_matrix_loader import find_rule, load_rules_from_csv, sync_policy_documents_from_rule_matrix
from schemas.genai_output_schema import GenAIComplaintAnalysis

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "sample_complaints" / "sample_complaints.csv"
RULE_MATRIX_PATH = ROOT / "complaint_rules" / "rule_matrix.csv"
OUT_CSV = ROOT / "reports" / "genai_vs_python_comparison.csv"
OUT_MD = ROOT / "reports" / "genai_vs_python_comparison.md"


def load_dataset_rows(limit: int):
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # Only "standard" and adversarial case types map to a single rule-matrix
    # entry, which is what a row-by-row comparison needs; ambiguous/duplicate
    # rows are multi-issue by design and are covered separately in the report.
    usable = [r for r in rows if r["case_type"] in ("standard", "prompt_injection", "contradictory_policy")]
    random.Random(7).shuffle(usable)
    return usable[:limit]


def run(limit: int, live: bool):
    init_db()
    db = SessionLocal()

    if db.query(Complaint).count() == 0 or True:
        load_rules_from_csv(db, str(RULE_MATRIX_PATH))
        sync_policy_documents_from_rule_matrix(db, str(RULE_MATRIX_PATH))

    rows = load_dataset_rows(limit)
    comparison_rows = []

    if live:
        from genai_pipeline.pipeline import analyze_complaint

    for i, row in enumerate(rows):
        complaint = Complaint(customer_email=row["customer_email"], raw_text=row["text"])
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        rule = find_rule(db, row["expected_category"], row["expected_subcategory"]) \
            if row["case_type"] == "standard" else None

        if live:
            analysis, analysis_record = analyze_complaint(db, complaint)
        else:
            raw = simulate_analysis(row["text"], rule, is_injection_case=(row["case_type"] == "prompt_injection"), seed=i)
            raw.pop("_simulated_complied_with_injection", None)
            analysis = GenAIComplaintAnalysis.model_validate(raw)
            from database.models import GenAIAnalysis
            analysis_record = GenAIAnalysis(complaint_id=complaint.id, prompt_version="simulated_v1",
                                             provider="simulate", model="rule-based-simulator",
                                             raw_json=analysis.model_dump_json())
            db.add(analysis_record)
            db.commit()
            db.refresh(analysis_record)

        outcome = validate_analysis(db, complaint, analysis, analysis_record)
        comparison_rows.append(build_comparison_row(complaint.id, analysis, outcome))
        comparison_rows[-1]["case_type"] = row["case_type"]

    db.close()
    write_report(comparison_rows, live)


def write_report(rows: list[dict], live: bool):
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    matches = sum(1 for r in rows if r["match"])
    mismatches = total - matches
    review = sum(1 for r in rows if r["requires_manual_review"])
    by_flag = {}
    for r in rows:
        for flag in [f.strip() for f in r["risk_flags"].split(",") if f.strip()]:
            by_flag[flag] = by_flag.get(flag, 0) + 1

    injection_rows = [r for r in rows if r["case_type"] == "prompt_injection"]
    injection_caught = sum(1 for r in injection_rows if r["requires_manual_review"] or not r["match"])

    lines = [
        "# GenAI vs. Python Validation — Comparison Report",
        "",
        f"Mode: {'LIVE (real Anthropic API)' if live else 'SIMULATED (offline, for structure/demo — re-run with --live before submission)'}",
        f"Total cases: {total}",
        "",
        "## Summary",
        f"- Matches (GenAI and Python agreed): {matches} ({matches/total:.0%})",
        f"- Mismatches (Python overrode/flagged GenAI): {mismatches} ({mismatches/total:.0%})",
        f"- Routed to manual review: {review} ({review/total:.0%})",
        "",
        "## Risk flags raised by Pipeline 2",
        *[f"- {flag}: {count}" for flag, count in sorted(by_flag.items(), key=lambda x: -x[1])],
        "",
        "## Prompt-injection subset",
        f"- Injection cases in this run: {len(injection_rows)}",
        f"- Caught by Pipeline 2 (flagged mismatch or manual review): {injection_caught}/{len(injection_rows)}",
        "",
        "Full row-by-row detail: `reports/genai_vs_python_comparison.csv`",
    ]
    OUT_MD.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    run(args.limit, args.live)
