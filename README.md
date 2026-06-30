# Multi-Source Candidate Data Transformer

Production-ready pipeline for the **Eightfold Engineering Intern (Jul–Dec 2026)** assignment. Ingests structured and unstructured candidate sources, merges them into a canonical profile with provenance and confidence, then projects to a runtime-configurable output schema.

## Tech Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Language | **Python 3.11+** | Strong data/ETL ecosystem, fast to iterate |
| CLI | **Typer** | Typed, production-friendly CLI |
| Schemas | **Pydantic v2** | Canonical + config validation |
| Phones | **phonenumbers** | Reliable E.164 normalization |
| Dates | **python-dateutil** | Robust date parsing |
| Resume | **pypdf**, **python-docx** | PDF/DOCX text extraction |
| GitHub | **requests** | Optional live API (sample JSON fallback) |
| Tests | **pytest** | Unit + end-to-end coverage |

## Architecture (Service Folders)

```
src/candidate_transformer/
├── cli/           # CLI entrypoint
├── ingest/        # CSV, ATS JSON, GitHub, resume, notes
├── extract/       # Path resolution for projection
├── normalize/     # Phone, date, skill, location normalizers
├── merge/         # Conflict resolution + deduplication
├── confidence/    # Overall confidence scoring
├── project/       # Configurable output projection layer
├── validate/      # Schema validation
├── models/        # Canonical + config Pydantic models
└── pipeline/      # Orchestrator (detect → validate)
```

**Pipeline flow:** detect → ingest → normalize → merge → confidence → project → validate

## Quick Start

```bash
cd eightfold-candidate-transformer
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
```

### Default canonical output

```bash
python -m candidate_transformer \
  data/samples/recruiter.csv \
  data/samples/ats.json \
  data/samples/github_profile.json \
  data/samples/resume.txt \
  data/samples/recruiter_notes.txt \
  -o output/default_profile.json
```

### Custom projection config

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

## Source Types Implemented

| Type | Source | Folder |
| --- | --- | --- |
| Structured | Recruiter CSV | `ingest/csv_ingestor.py` |
| Structured | ATS JSON blob | `ingest/json_ingestor.py` |
| Unstructured | GitHub profile (JSON file or live URL) | `ingest/github_ingestor.py` |
| Unstructured | Resume (TXT/PDF/DOCX) | `ingest/resume_ingestor.py` |
| Unstructured | Recruiter notes (.txt) | `ingest/notes_ingestor.py` |

## Merge & Confidence Policy

- **Match keys:** primary email, fallback normalized full name
- **Conflict resolution:** structured sources beat unstructured; higher per-field confidence wins
- **Never invent data:** missing/garbage inputs become `null` or are omitted
- **Provenance:** every merged field records `{ field, source, method, confidence }`
- **Overall confidence:** weighted average across key fields, adjusted for multi-source agreement

## Custom Output Config

See `config/custom_output.json`:

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

Supported `on_missing` values: `null`, `omit`, `error`.

## Tests

```bash
pytest -q
```

## Assumptions & Descoped Items

- GitHub live API is optional; sample JSON is used for deterministic demo runs
- LinkedIn scraping is not implemented (ToS constraints); links are taken from ATS/notes
- Resume parsing uses heuristics, not ML/NLP models
- Single-candidate merge per run (batch folder processing can be added as a thin wrapper)
- Location parsing is rule-based, not geocoded

## Demo Video Checklist

1. Run default transform command and show `output/default_profile.json`
2. Run custom config command and show projected fields
3. Explain merge policy (structured > unstructured) and one edge case (invalid phone → omitted)
