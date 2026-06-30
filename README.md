# Multi-Source Candidate Data Transformer

Ingests candidate data from multiple structured and unstructured sources, merges them into a canonical profile with provenance and confidence, and projects the result to a runtime-configurable output schema.

**Author:** Abhinav Patel · IIIT Bhopal  
**Live demo:** https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/

---

## Overview

This project implements an end-to-end candidate data pipeline for the Eightfold Engineering Intern assignment. It supports recruiter CSV exports, ATS JSON, GitHub profiles, resumes, and free-form notes, producing a normalized canonical profile that can be reshaped at runtime without modifying the core engine.

**Pipeline:** detect → ingest → normalize → merge → confidence → project → validate

**Sample inputs** model a fresher profile: Abhinav Patel, B.Tech CSE at IIIT Bhopal (2026), with an internship at TechNova Solutions, Bhopal, India.

---

## Features

- Multi-source ingestion (structured + unstructured)
- Normalization: E.164 phones, YYYY-MM dates, canonical skills, ISO-3166 countries
- Merge with conflict resolution and full provenance tracking
- Weighted overall confidence score
- Configurable output projection (`OutputConfig` JSON)
- CLI, REST API, and Streamlit web UI

---

## Installation

```bash
git clone https://github.com/Abhinav3289/eightfold_assignment_candidate-profile_transformers-.git
cd eightfold_assignment_candidate-profile_transformers-

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -e ".[dev]"
```

---

## Usage

### CLI

Default canonical output:

```bash
python -m candidate_transformer \
  data/samples/recruiter.csv \
  data/samples/ats.json \
  data/samples/github_profile.json \
  data/samples/resume.txt \
  data/samples/recruiter_notes.txt \
  -o output/default_profile.json
```

Custom projection:

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

Open http://localhost:8501. The UI supports sample data, file upload, and manual form entry.

### REST API

```bash
pip install -r requirements-api.txt
uvicorn candidate_transformer.api.main:app --reload --port 8000
```

API documentation: http://localhost:8000/docs

```bash
curl -X POST http://localhost:8000/api/v1/transform/samples \
  -H "Content-Type: application/json" \
  -d "{\"use_custom_example\": true}"
```

---

## Project Structure

```
src/candidate_transformer/
├── cli/           # Typer CLI
├── ingest/        # Source parsers (CSV, JSON, GitHub, resume, notes, manual)
├── normalize/     # Phone, date, skill, location normalizers
├── merge/         # Conflict resolution and deduplication
├── confidence/    # Overall confidence scoring
├── project/       # Output projection layer
├── validate/      # Schema validation
├── api/           # FastAPI application
├── models/        # Pydantic models
└── pipeline/      # Orchestrator

web/app.py         # Streamlit UI
config/            # Output projection configs
data/samples/      # Sample input files
output/            # Generated profile JSON
docs/              # Design document (PDF)
tests/             # Unit and integration tests
```

---

## Design

### Canonical schema

`candidate_id`, `full_name`, `emails[]`, `phones[]`, `location`, `links`, `headline`, `years_experience`, `skills[]`, `experience[]`, `education[]`, `provenance[]`, `overall_confidence`

### Merge policy

- Match candidates by normalized email, then full name
- Structured sources take precedence over unstructured sources
- Within the same tier, higher per-field confidence wins
- List fields are unioned and deduplicated
- Missing or invalid values become `null`; data is never invented

### Configurable output

The projection layer accepts a runtime JSON config for field selection, remapping (`from`), per-field normalization, and missing-value behavior (`null`, `omit`, `error`). The internal canonical record remains unchanged.

`overall_confidence` is computed on the full merged profile and passed through to projected output.

Example config: [`config/custom_output.json`](config/custom_output.json)

### Technical design document

[`docs/Abhinav_Patel_Eightfold_Design_Only.pdf`](docs/Abhinav_Patel_Eightfold_Design_Only.pdf)

---

## Sample Output

| Output | File |
| --- | --- |
| Default canonical profile | [`output/default_profile.json`](output/default_profile.json) |
| Custom projection | [`output/custom_profile.json`](output/custom_profile.json) |

---

## Tests

```bash
pytest -q
```

---

## Tech Stack

Python 3.11+ · Typer · FastAPI · Streamlit · Pydantic v2 · phonenumbers · python-dateutil · pypdf · python-docx · pytest

---

## Deployment

The web UI is deployed on Streamlit Cloud. Docker and Render configurations are included (`Dockerfile`, `Dockerfile.api`, `render.yaml`).

---

## Limitations

- GitHub ingestion uses bundled sample JSON by default; live API fetch is supported but optional
- LinkedIn profile scraping is not implemented
- Resume parsing is heuristic-based
- Single-candidate processing per run
- Location parsing is rule-based

---

## License

Submitted as part of the Eightfold Engineering Intern (Jul–Dec 2026) technical assessment.
