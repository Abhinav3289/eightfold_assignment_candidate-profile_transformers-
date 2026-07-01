# Multi-Source Candidate Data Transformer

Ingests candidate data from multiple structured and unstructured sources, merges them into a canonical profile with provenance and confidence, and projects the result to a runtime-configurable output schema.

**Author:** Abhinav Patel · IIIT Bhopal  
**Live demo:** https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/  
**Demo video:** https://drive.google.com/file/d/1JS8tHBY1qeoK1qqsJlR7GcSrVzkdQjoG/view?usp=sharing

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

[`docs/Abhinav_Patel_Eightfold.pdf`](docs/Abhinav_Patel_Eightfold.pdf) — includes HLD and pipeline flow diagrams.  
[`docs/Abhinav_Patel_Eightfold.docx`](docs/Abhinav_Patel_Eightfold.docx) — same content in Word format for submission.

**Demo video script (~2 min, PDF):** [`docs/Abhinav_Patel_Demo_Video_Script.pdf`](docs/Abhinav_Patel_Demo_Video_Script.pdf)  
**Demo walkthrough video:** https://drive.google.com/file/d/1JS8tHBY1qeoK1qqsJlR7GcSrVzkdQjoG/view?usp=sharing

Regenerate PDF: `pip install -r docs/requirements-pdf.txt && python docs/generate_pdf.py`  
Regenerate DOCX: `python docs/generate_docx.py`

---

## Sample Demo: Input & Output

The bundled sample models **Abhinav Patel** — B.Tech CSE (final year) at IIIT Bhopal, with an internship at TechNova Solutions, Bhopal, India. Run with **Use sample data** in the web UI, or pass the files below via CLI.

### Input sources

| Source | File | Type |
| --- | --- | --- |
| Recruiter export | [`data/samples/recruiter.csv`](data/samples/recruiter.csv) | Structured CSV |
| ATS record | [`data/samples/ats.json`](data/samples/ats.json) | Structured JSON |
| GitHub profile | [`data/samples/github_profile.json`](data/samples/github_profile.json) | Unstructured JSON |
| Resume | [`data/samples/resume.txt`](data/samples/resume.txt) | Unstructured text |
| Recruiter notes | [`data/samples/recruiter_notes.txt`](data/samples/recruiter_notes.txt) | Free-form text |

**Recruiter CSV** (`data/samples/recruiter.csv`):

```csv
name,email,phone,current_company,title,location
Abhinav Patel,abhinav.patel@example.com,+91 98765 43210,IIIT Bhopal,B.Tech CSE Student (Final Year),"Bhopal, Madhya Pradesh, IN"
```

**ATS JSON** (excerpt from `data/samples/ats.json`):

```json
{
  "candidate_name": "Abhinav Patel",
  "contact_email": "abhinav.patel@example.com",
  "mobile": "+919876543210",
  "skill_tags": ["python", "java", "javascript", "react", "sql", "django", "git"],
  "work_history": [
    {
      "employer": "TechNova Solutions",
      "role": "Software Engineering Intern",
      "start_date": "May 2025",
      "end_date": "Jul 2025"
    }
  ],
  "education_history": [
    {
      "school": "IIIT Bhopal",
      "degree": "B.Tech",
      "major": "Computer Science and Engineering",
      "graduation_year": 2026
    }
  ]
}
```

**GitHub profile** (excerpt from `data/samples/github_profile.json`):

```json
{
  "login": "abhinav3289",
  "name": "Abhinav Patel",
  "bio": "B.Tech CSE @ IIIT Bhopal | Python, Java, React | Aspiring SDE",
  "languages": ["Python", "Java", "JavaScript", "HTML", "CSS"]
}
```

**Resume** (excerpt from `data/samples/resume.txt`):

```text
Abhinav Patel
abhinav.patel@example.com | +91-9876543210 | Bhopal, Madhya Pradesh, India

Skills: Python, Java, JavaScript, React, SQL, Django, Git, REST APIs

Experience: Software Engineering Intern - TechNova Solutions (May 2025 - Jul 2025)
Education: B.Tech CSE - IIIT Bhopal (2026)
```

**Recruiter notes** (`data/samples/recruiter_notes.txt`):

```text
Candidate: Abhinav Patel (abhinav.patel@example.com)
Promising fresher from IIIT Bhopal. Strong Python and DSA fundamentals. 1 internship completed.
Notes: Good communicator, open to full-time SDE roles across India.
```

### Default canonical output

Pipeline merges all five sources into one profile with provenance and confidence. Full output: [`output/default_profile.json`](output/default_profile.json).

```json
{
  "candidate_id": "cand_5034ad715b57",
  "full_name": "Abhinav Patel",
  "emails": ["abhinav.patel@example.com"],
  "phones": ["+919876543210"],
  "location": {
    "city": "Bhopal",
    "region": "Madhya Pradesh",
    "country": "IN"
  },
  "headline": "B.Tech CSE Student (Final Year)",
  "years_experience": 1.0,
  "skills": [
    { "name": "Python", "confidence": 0.8, "sources": ["ats", "github_profile", "resume", "recruiter_notes"] },
    { "name": "Java", "confidence": 0.8, "sources": ["ats", "github_profile", "resume"] },
    { "name": "React", "confidence": 0.8, "sources": ["ats", "resume"] }
  ],
  "experience": [
    {
      "company": "TechNova Solutions",
      "title": "Software Engineering Intern",
      "start": "2025-05",
      "end": "2025-07",
      "summary": "Built REST APIs and internal dashboards using Python and React."
    }
  ],
  "education": [
    {
      "institution": "IIIT Bhopal",
      "degree": "B.Tech",
      "field": "Computer Science and Engineering",
      "end_year": 2026
    }
  ],
  "overall_confidence": 0.918
}
```

Key normalizations applied: phone `+91 98765 43210` → `+919876543210` (E.164), dates `May 2025` → `2025-05`, skills `python`/`py` → `Python`. Every field includes full provenance in the complete JSON file.

### Custom projection output

Same canonical record, projected with [`config/custom_output.json`](config/custom_output.json). Full output: [`output/custom_profile.json`](output/custom_profile.json).

```json
{
  "full_name": "Abhinav Patel",
  "primary_email": "abhinav.patel@example.com",
  "phone": "+919876543210",
  "skills": [
    "Python", "Java", "JavaScript", "React", "SQL",
    "Django", "Git", "HTML", "CSS", "REST APIs"
  ],
  "overall_confidence": 0.918
}
```

`overall_confidence` stays **0.918** in both outputs because it is computed on the full merged profile before projection.

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
