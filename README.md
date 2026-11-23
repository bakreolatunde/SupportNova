# SupportNova

Generative-AI-powered complaint management system with an independent,
non-GenAI Python validation layer (Complaint Resolution Rule Matrix).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY (or your chosen provider)
```

## Load sample data

```python
from database.session import SessionLocal, init_db
from python_validation.rule_matrix_loader import load_rules_from_csv

init_db()
db = SessionLocal()
load_rules_from_csv(db, "complaint_rules/rule_matrix.csv")
```

Regenerate the 500+ complaint dataset any time with:

```bash
python scripts/generate_dataset.py
```

Covers 10 categories / 27 subcategories / 8 departments, 22 prompt-injection
cases, 26 ambiguous/multi-issue, 21 contradictory-policy, and 27 near-duplicate
pairs — see `sample_complaints/sample_complaints.csv`.

## Run the API

```bash
uvicorn src.main:app --reload
```

- `POST /complaints` — submit a complaint, runs both pipelines synchronously
- `GET /complaints/{id}` — fetch a complaint
- `GET /admin/review-queue` — items awaiting human review (JSON)
- `POST /auth/register`, `POST /auth/login`, `POST /auth/logout` — API auth (JWT, returned + set as an httpOnly cookie)

## Dashboards (role-based, server-rendered)

Visit `/login-page` (or `/register-page` to create an account) — after login
you're redirected by role:

| Role | Page | Shows |
| --- | --- | --- |
| customer | `/dashboard/customer` | A submission form + their own complaint history |
| agent | `/dashboard/agent` | The manual review queue, with a resolve action |
| admin | `/dashboard/admin` | Complaint/escalation stats, rule matrix + policy counts, recent complaints |

Design: `src/static/styles.css` — a small token-based system (ink/muted/brand
+ 4 urgency colors), Space Grotesk for headings and IBM Plex Sans for body,
severity shown as a colored left-rail on table rows rather than badge pills.
Wrong-role access returns 403; no session returns 401 on the API / redirects
you to log in on the dashboard routes.

## Run tests

```bash
pytest
```

## Reports & security testing

```bash
python scripts/generate_comparison_report.py        # simulated, no API cost — writes reports/genai_vs_python_comparison.{csv,md}
python scripts/generate_comparison_report.py --live  # uses your real ANTHROPIC_API_KEY instead
python scripts/run_security_tests.py                 # writes reports/security_adversarial_test_report.md
```

Both default to a local **simulated** GenAI client (`genai_pipeline/simulate.py`)
so they run free and fast for development/CI. It deliberately injects noise
(misrouting, missed escalations, a model that "complies" with prompt
injection) so Pipeline 2's independence is actually exercised, not just
demonstrated on easy cases. **Re-run with `--live` before submission** —
the SRS deliverable needs real GenAI output, not simulated.

## Deployment

See `documentation/deployment.md` for Docker / Render / Railway / Fly.io.
Quick local Docker run: `docker compose up --build` (needs `.env` filled in first).

## Diagrams

DFD, use case, activity, and sequence diagrams are in `documentation/diagrams.md`
as Mermaid (renders natively on GitHub) — also embedded in the Report Skeleton doc.

## Repo layout

| Folder | Purpose |
| --- | --- |
| `genai_pipeline/` | Pipeline 1 — GenAI complaint analysis |
| `python_validation/` | Pipeline 2 — independent rule-based validation |
| `comparison_engine/` | Builds the GenAI-vs-Python comparison report |
| `complaint_rules/` | The hand-authored Rule Matrix (ground truth) |
| `knowledge_base/` | Policy document ingestion, chunking, retrieval |
| `security/` | Prompt-injection guarding |
| `database/`, `schemas/` | ORM models and Pydantic contracts |
| `src/` | FastAPI application + Jinja2 dashboard templates |
| `auth/` | Password hashing (bcrypt) + JWT issuance/verification, role dependency |
| `sample_complaints/`, `sample_documents/` | 540-row generated dataset + starter policy doc |
| `scripts/` | `generate_dataset.py` — reproducible dataset generator |
| `hidden_test_ready/` | Notes on how new data is added without code changes |

See the **Build Plan** and **Report Skeleton** docs for the day-by-day
sequence and the Project Report structure.
