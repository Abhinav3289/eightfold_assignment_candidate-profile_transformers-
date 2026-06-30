# Technical Design — Multi-Source Candidate Data Transformer

**Abhinav Patel | Eightfold Engineering Intern (Jul–Dec 2026)**

---

## 1. Pipeline Breakdown

```
Detect → Ingest → Normalize → Merge → Confidence → Project → Validate
```

| Stage | Responsibility |
| --- | --- |
| **Detect** | Route input by file type (CSV, ATS JSON, GitHub JSON, resume, notes) |
| **Ingest** | Extract fields into `SourceRecord` with per-field confidence |
| **Normalize** | E.164 phones, YYYY-MM dates, canonical skills, ISO-3166 countries |
| **Merge** | Match by email/name; resolve conflicts; dedupe lists |
| **Confidence** | Weighted score from field provenance + multi-source bonus |
| **Project** | Apply runtime JSON config (field select, rename, normalize, on_missing) |
| **Validate** | Pydantic validation on canonical and projected output |

---

## 2. Canonical Schema & Normalization

| Field | Normalization |
| --- | --- |
| `phones[]` | E.164 via `phonenumbers` |
| `experience[].start/end` | `YYYY-MM` via dateutil + regex |
| `skills[].name` | Alias map (e.g. `k8s` → `Kubernetes`, `py` → `Python`) |
| `location.country` | ISO-3166 alpha-2 (`US`, `IN`, `GB`) |
| `emails[]` | Lowercase, deduplicated |

Internal model: `CanonicalProfile` with `provenance[]` and `overall_confidence`.

---

## 3. Merge & Conflict Resolution

**Matching:** Primary key = normalized email; fallback = normalized full name.

**Winner policy (per scalar field):**
1. Structured source beats unstructured
2. Higher per-field confidence wins within same tier

**Collections:** Union + dedupe (emails, phones, skills). Experience/education merged by `(company, title)` or `(institution, degree)` keys; enrich null fields from lower-priority sources.

**Confidence:** Weighted average over key fields (name, email, phone, skills, experience, education). +0.05 if ≥3 sources agree; −0.05 if only one source.

**Principle:** Wrong-but-confident is worse than honestly empty — never invent data.

---

## 4. Configurable Output Layer

Runtime `OutputConfig` JSON separates internal canonical record from external shape:

- **Field selection** via `path`
- **Remapping** via `"from": "emails[0]"` or `"skills[].name"`
- **Normalization** per field: `E164`, `canonical`
- **Metadata toggles:** `include_provenance`, `include_confidence`
- **Missing values:** `null` | `omit` | `error`

Projected output validated before return.

---

## 5. Edge Cases

| Case | Handling |
| --- | --- |
| Invalid phone | Normalizer returns `null`; field omitted from `phones[]` |
| Conflicting titles (structured vs notes) | Structured CSV/ATS wins over unstructured notes |
| Missing entire source | Pipeline continues; confidence reflects sparse provenance |
| Malformed JSON/empty CSV | Source skipped gracefully; error only if zero valid records |
| Duplicate experience rows | Deduped by company+title; richer entry fills null dates |

**Descoped under time pressure:** LinkedIn scraping, ML resume parsing, batch multi-candidate folder processing, geocoding.

---

## 6. Architecture

Modular Python services: `ingest/`, `normalize/`, `merge/`, `confidence/`, `project/`, `validate/`, `pipeline/`. Interfaces: CLI (Typer), REST API (FastAPI), Web UI (Streamlit).

**Deterministic:** Same inputs → same output. Every value traceable via `provenance`.

---

*Export this document to PDF as `Abhinav_Patel_<YourEmail>_Eightfold.pdf` for Stage 1 submission.*
