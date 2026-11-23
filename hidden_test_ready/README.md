# Hidden Evaluation Readiness

This project is designed so the evaluator's hidden complaint/document pack
can be processed WITHOUT modifying core source code:

- New categories/subcategories/departments → add rows to `complaint_rules/rule_matrix.csv`
  (or the `rule_matrix_entries` table) and `routing_rules/routing_config.json`.
- New policy documents → upload through `knowledge_base/ingestion.py` (or the
  admin upload endpoint once built) — no parsing code changes needed.
- New escalation triggers → add to `escalation_rules/escalation_config.json`
  and, if keyword-based, extend `CRITICAL_KEYWORDS` in
  `python_validation/escalation_checker.py` (flagged here as the one place
  still in code — move to config before submission if time allows).

Before submission: run the full sample_complaints + hidden-style edge cases
through both pipelines and confirm no core file needed a line changed.
