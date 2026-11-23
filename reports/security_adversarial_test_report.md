# Security / Adversarial Testing Report

Scenario: 22 prompt-injection complaints, each run against a simulated GenAI response that DELIBERATELY complies with the injected instruction (worst case — model already fooled). Tests whether either safety layer still catches it.

## Results
- Layer 1 (pre-send heuristic flag): 22/22 (100%)
- Layer 2 (Pipeline 2 catches the compromised output): 22/22 (100%)
- Caught by at least one layer: 22/22
- Missed by BOTH layers: 0

No case was missed by both layers in this run.

## Interpretation
Layer 1 existing or not doesn't matter for safety — it's a cheap early flag for logging/alerting. Layer 2 is the real guarantee: it inspects the GenAI OUTPUT, not the input, so it catches compliance with an injection attempt regardless of whether the phrasing matched a known pattern.