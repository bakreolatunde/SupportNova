# GenAI vs. Python Validation — Comparison Report

Mode: SIMULATED (offline, for structure/demo — re-run with --live before submission)
Total cases: 150

## Summary
- Matches (GenAI and Python agreed): 121 (81%)
- Mismatches (Python overrode/flagged GenAI): 29 (19%)
- Routed to manual review: 18 (12%)

## Risk flags raised by Pipeline 2
- no_rule_matrix_entry: 18
- unsupported_promise: 11

## Prompt-injection subset
- Injection cases in this run: 11
- Caught by Pipeline 2 (flagged mismatch or manual review): 11/11

Full row-by-row detail: `reports/genai_vs_python_comparison.csv`