# Multi-Source Candidate Data Transformer

**Abhinav Patel · IIIT Bhopal · Eightfold Engineering Intern (Jul–Dec 2026)**

A production-ready pipeline that ingests structured and unstructured candidate sources, merges them into a canonical profile with **provenance** and **confidence**, and projects to a **runtime-configurable** output schema.

---

## Submission Links

| Deliverable | Link |
| --- | --- |
| **Live Demo (Web UI)** | https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/ |
| **GitHub Repository** | https://github.com/Abhinav3289/eightfold_assignment_candidate-profile_transformers- |
| **Design Document (PDF)** | [`docs/Abhinav_Patel_Eightfold_Design_Only.pdf`](docs/Abhinav_Patel_Eightfold_Design_Only.pdf) |
| **Design + Demo Script (PDF)** | [`docs/Abhinav_Patel_Eightfold.pdf`](docs/Abhinav_Patel_Eightfold.pdf) |
| **Sample Output (default)** | [`output/default_profile.json`](output/default_profile.json) |
| **Sample Output (custom)** | [`output/custom_profile.json`](output/custom_profile.json) |
| **Demo Video** | _[Add your YouTube/Loom link here]_ |

> Rename the design PDF to `Abhinav_Patel_<YourEmail>_Eightfold.pdf` before email submission.

---

## What This Project Does

| Capability | Details |
| --- | --- |
| **Structured sources** | Recruiter CSV, ATS JSON |
| **Unstructured sources** | GitHub profile, resume (TXT/PDF/DOCX), recruiter notes |
| **Normalization** | E.164 phones, YYYY-MM dates, canonical skills, ISO-3166 countries |
| **Merge policy** | Structured beats unstructured; higher confidence wins; never invent data |
| **Configurable output** | Runtime JSON config — field select, rename, normalize, `on_missing` |
| **Interfaces** | CLI · REST API (FastAPI) · Web UI (Streamlit) |

**Sample candidate:** Abhinav Patel — B.Tech CSE, IIIT Bhopal (2026), intern at TechNova Solutions, Bhopal IN.

**Pipeline:** `detect → ingest → normalize → merge → confidence → project → validate`

---

## Quick Start (Local)

```bash
git clone https://github.com/Abhinav3289/eightfold_assignment_candidate-profile_transformers-.git
cd eightfold_assignment_candidate-profile_transformers-

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -e ".[dev]"
pytest -q
```

### CLI — default canonical output

```bash
python -m candidate_transformer \
  data/samples/recruiter.csv \
  data/samples/ats.json \
  data/samples/github_profile.json \
  data/samples/resume.txt \
  data/samples/recruiter_notes.txt \
  -o output/default_profile.json
```

### CLI — custom projection config

```bash
python -m candidate_transformer \
  data/samples/recruiter.csv \
  data/samples/ats.json \
  data/samples/github_profile.json \
  data/samples/resume.txt \
  data/samples/recruiter_notes.txt \
  -c config/custom_output.json \
  -o output/custom_profile.json
```

### Web UI

```bash
pip install -r requirements-web.txt
streamlit run web/app.py
```

Open **http://localhost:8501** — or use the [live demo](https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/) (no install required).

**Input modes:** Use sample data · Upload files · Manual entry form

### REST API

```bash
pip install -r requirements-api.txt
uvicorn candidate_transformer.api.main:app --reload --port 8000
```

Swagger UI: **http://localhost:8000/docs**

```bash
# Quick test with bundled sample data
curl -X POST http://localhost:8000/api/v1/transform/samples \
  -H "Content-Type: application/json" \
  -d "{\"use_custom_example\": true}"
```

---

## Architecture

```
src/candidate_transformer/
├── cli/           # Typer CLI
├── ingest/        # CSV, ATS JSON, GitHub, resume, notes, manual form
├── normalize/     # Phone, date, skill, location
├── merge/         # Conflict resolution + deduplication
├── confidence/    # Overall confidence scoring
├── project/       # Configurable output projection
├── validate/      # Schema validation
├── api/           # FastAPI REST layer
├── models/        # Pydantic schemas
└── pipeline/      # Orchestrator
```

---

## Merge & Confidence Policy

- **Match keys:** normalized email (primary), full name (fallback)
- **Conflict resolution:** structured sources beat unstructured; higher per-field confidence wins
- **Provenance:** every field records `{ field, source, method, confidence }`
- **Overall confidence:** weighted average over key fields; +0.05 if ≥3 sources agree
- **Principle:** wrong-but-confident is worse than honestly empty — missing/garbage → `null`

> Custom projection copies `overall_confidence` from the full canonical merge — it is not recalculated for the smaller output subset.

---

## Custom Output Config

See [`config/custom_output.json`](config/custom_output.json):

```json
{
  "fields": [
    { "path": "full_name", "type": "string", "required": true },
    { "path": "primary_email", "from": "emails[0]", "type": "string", "required": true },
    { "path": "phone", "from": "phones[0]", "type": "string", "normalize": "E164" },
    { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical" }
  ],
  "include_confidence": true,
  "on_missing": "null"
}
```

Supported `on_missing` values: `null` · `omit` · `error`

---

## Tests

```bash
pytest -q
# 15 tests — normalizers, merge, projection, pipeline, API, manual ingestor
```

---

## Tech Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.11+ |
| CLI | Typer |
| API | FastAPI + Uvicorn |
| Web UI | Streamlit |
| Schemas | Pydantic v2 |
| Phones | phonenumbers (E.164) |
| Dates | python-dateutil |
| Resume | pypdf, python-docx |
| Tests | pytest |

---

## Deploy

| Platform | File | URL |
| --- | --- | --- |
| Streamlit Cloud | `web/app.py` + `requirements-web.txt` | [Live demo](https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/) |
| Render | `render.yaml` + `Dockerfile` / `Dockerfile.api` | Blueprint deploy |

Regenerate design PDF:

```bash
python docs/generate_pdf.py
```

---

## Assumptions & Descoped

- GitHub live API is optional; sample JSON used for deterministic demos
- LinkedIn scraping not implemented (ToS); links sourced from ATS/notes
- Resume parsing uses heuristics, not ML/NLP
- Single-candidate merge per run (no batch folder processing)
- Location parsing is rule-based, not geocoded

---

## Demo Video Guide

Full voiceover script: [`docs/Abhinav_Patel_Eightfold.pdf`](docs/Abhinav_Patel_Eightfold.pdf) (Page 2)

1. Live app → **Use sample data** → default JSON (provenance + confidence)
2. **Custom projection config** → show `primary_email`, `phone`, flattened `skills`
3. Explain: structured > unstructured merge policy
4. Edge case: invalid phone → `null`, never invented
5. Show GitHub + `pytest -q` passing

---

## Author

**Abhinav Patel**  
Indian Institute of Information Technology Bhopal (IIIT Bhopal)  
Eightfold Engineering Intern Assignment · Jul–Dec 2026
