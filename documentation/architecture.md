# Architecture Notes (working doc — expand into the Project Report's §3)

```mermaid
flowchart LR
  A[Customer submits complaint] --> B[complaint_processing: clean + dedupe]
  B --> C[genai_pipeline: Pipeline 1]
  C --> D[python_validation: Pipeline 2]
  D -->|match| E[Auto-resolve / respond]
  D -->|mismatch or new category| F[Manual Review Queue]
  D --> G[comparison_engine: log GenAI vs Python row]
```

- Two pipelines never share a verdict path: Pipeline 1 proposes, Pipeline 2 disposes.
- `knowledge_base/` and `complaint_rules/rule_matrix.csv` are the only sources
  of truth Pipeline 2 is allowed to check against — never Pipeline 1's own output.
