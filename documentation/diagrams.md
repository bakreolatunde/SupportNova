# Diagrams

Source of truth for the Project Report's §3.4–3.7. Mermaid renders natively
on GitHub — copy these blocks straight into the report.

## 3.4 Data Flow Diagram (Level 0 — Context)

```mermaid
flowchart LR
  Customer((Customer)) -->|submits complaint| SN[SupportNova System]
  SN -->|response / status| Customer
  Agent((Agent)) -->|reviews queue| SN
  Admin((Admin)) -->|manages rules & policies| SN
  SN -->|analysis request| GenAI[(GenAI API)]
  GenAI -->|structured JSON| SN
```

## 3.4 Data Flow Diagram (Level 1)

```mermaid
flowchart TB
  A[Complaint Submitted] --> B[1.0 Preprocess & Dedupe]
  B --> C[(Complaints DB)]
  B --> D[2.0 Pipeline 1: GenAI Analysis]
  D <--> E[(Knowledge Base / Policy Chunks)]
  D --> F[(GenAI Analyses DB)]
  D --> G[3.0 Pipeline 2: Python Validation]
  G <--> H[(Rule Matrix DB)]
  G --> I[(Validation Results DB)]
  G -->|match| J[4.0 Auto-Resolve & Respond]
  G -->|mismatch| K[5.0 Manual Review Queue]
  G --> L[6.0 Comparison Engine]
  L --> M[(Comparison Report)]
```

## 3.5 Use Case Diagram

```mermaid
flowchart LR
  Customer((Customer))
  Agent((Agent))
  Admin((Admin))

  Customer --> UC1[Submit Complaint]
  Customer --> UC2[View Complaint Status]
  Agent --> UC3[Review Flagged Complaints]
  Agent --> UC4[Resolve Review Item]
  Admin --> UC5[Upload Policy Documents]
  Admin --> UC6[Manage Rule Matrix]
  Admin --> UC7[View System Analytics]
  Admin --> UC3
```

## 3.6 Activity Diagram — Complaint Lifecycle

```mermaid
flowchart TD
  Start([Complaint submitted]) --> Clean[Clean & fingerprint text]
  Clean --> Dup{Near-duplicate?}
  Dup -- yes --> Link[Link to original complaint]
  Dup -- no --> Analyze[Pipeline 1: GenAI analysis]
  Link --> Analyze
  Analyze --> Validate[Pipeline 2: independent validation]
  Validate --> Match{Matches rule matrix\nand no risk flags?}
  Match -- yes --> AutoResolve[Auto-respond to customer]
  Match -- no --> Queue[Add to manual review queue]
  Queue --> HumanReview[Agent reviews]
  HumanReview --> Resolve[Mark resolved]
  AutoResolve --> Log[Log comparison row]
  Resolve --> Log
  Log --> End([Done])
```

## 3.7 Sequence Diagram — Complaint Submission

```mermaid
sequenceDiagram
  actor Customer
  participant API as FastAPI (/complaints)
  participant Pre as complaint_processing
  participant P1 as genai_pipeline (Pipeline 1)
  participant KB as Knowledge Base
  participant P2 as python_validation (Pipeline 2)
  participant DB as Database

  Customer->>API: POST /complaints {text}
  API->>Pre: clean_text, fingerprint, dedupe check
  Pre->>DB: query recent complaints
  API->>DB: save Complaint
  API->>P1: analyze_complaint(complaint)
  P1->>KB: retrieve_relevant_chunks(text)
  KB-->>P1: policy chunks
  P1->>P1: build prompt, wrap untrusted input
  P1-->>API: GenAIComplaintAnalysis (validated JSON)
  API->>P2: validate_analysis(analysis)
  P2->>DB: find_rule(category, subcategory)
  P2->>P2: check department, urgency, policy refs,\nescalation, unsupported promises
  P2-->>API: ValidationOutcome
  alt requires_manual_review
    API->>DB: create ReviewQueueItem
  end
  API-->>Customer: {status, analysis, validation}
```
