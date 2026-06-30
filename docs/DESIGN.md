# Technical Design — Multi-Source Candidate Data Transformer

**Abhinav Patel · IIIT Bhopal · Eightfold Engineering Intern (Jul–Dec 2026)**

---

### Problem
Merge candidate data from structured (recruiter CSV, ATS JSON) and unstructured (GitHub, resume, notes) sources into one **canonical profile** with **provenance**, **confidence**, and a **runtime-configurable** output layer.

### Pipeline: Detect → Ingest → Normalize → Merge → Confidence → Project → Validate

| Stage | Responsibility |
|-------|----------------|
| **Detect** | Route inputs by file type (CSV, JSON, resume, notes, GitHub URL) |
| **Ingest** | Extract fields into `SourceRecord` with per-field confidence |
| **Normalize** | E.164 phones · YYYY-MM dates · canonical skills · ISO-3166 countries |
| **Merge** | Match email/name · structured > unstructured · dedupe collections |
| **Confidence** | Weighted provenance score (+0.05 if ≥3 sources agree) |
| **Project** | Apply `OutputConfig` (select, rename, normalize, on_missing) |
| **Validate** | Pydantic validation on canonical and projected output |

### Canonical Schema
`candidate_id`, `full_name`, `emails[]`, `phones[]`, `location`, `links`, `headline`, `years_experience`, `skills[{name,confidence,sources}]`, `experience[]`, `education[]`, `provenance[]`, `overall_confidence`

### Merge Policy
- **Match:** normalized email (primary), full name (fallback)
- **Conflicts:** structured beats unstructured; higher field confidence wins
- **Collections:** union + dedupe; experience/education merged by key, nulls enriched from lower-priority source
- **Rule:** never invent data — missing/garbage → `null`

### Configurable Output
Runtime JSON separates internal canonical record from external shape: field selection, `"from"` remapping, per-field `E164`/`canonical` normalize, provenance/confidence toggles, `on_missing`: null | omit | error. Confidence is computed on full merge and copied to projected output.

### Edge Cases
Invalid phone → null · structured vs notes conflict → CSV/ATS wins · missing source → skip gracefully · duplicate roles → dedupe by company+title

**Descoped:** LinkedIn scraping, ML resume parsing, batch processing, geocoding.

### Architecture
Python modules: `ingest/`, `normalize/`, `merge/`, `confidence/`, `project/`, `validate/`, `pipeline/`, `api/`. Interfaces: CLI, FastAPI REST, Streamlit UI. Deterministic and fully traceable via provenance.

**Export as:** `Abhinav_Patel_<YourEmail>_Eightfold.pdf` · Full script: [`Abhinav_Patel_Eightfold_Submission.md`](Abhinav_Patel_Eightfold_Submission.md)
