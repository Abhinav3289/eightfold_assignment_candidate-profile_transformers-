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
├── api/           # FastAPI REST layer
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

## REST API

Run locally:

```bash
pip install -e ".[api]"
uvicorn candidate_transformer.api.main:app --reload --port 8000
```

Interactive docs: **http://localhost:8000/docs**

### Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/` | API metadata |
| `GET` | `/api/v1/config/example` | Example custom output config |
| `POST` | `/api/v1/transform` | Upload files (`multipart/form-data`) |
| `POST` | `/api/v1/transform/samples` | Run pipeline on bundled sample data |

### Example — sample data (JSON)

```bash
curl -X POST http://localhost:8000/api/v1/transform/samples \
  -H "Content-Type: application/json" \
  -d "{\"use_custom_example\": true}"
```

### Example — file upload

```bash
curl -X POST http://localhost:8000/api/v1/transform \
  -F "files=@data/samples/recruiter.csv" \
  -F "files=@data/samples/ats.json"
```

Optional form fields: `config_json`, `use_custom_example`, `include_provenance`, `include_confidence`.

Set `API_KEY` in the environment to require the `X-API-Key` header on protected routes.

Deploy API on Render using `Dockerfile.api`, or locally:

```bash
docker build -f Dockerfile.api -t candidate-transformer-api .
docker run -p 8000:8000 candidate-transformer-api
```

## Web UI (Visual Demo)

Run locally:

```bash
pip install -e ".[web]"
streamlit run web/app.py
```

Open `http://localhost:8501` — upload files or use bundled samples, then view JSON, provenance, and skills in the browser.

### Manual entry (no file upload)

1. Start the UI: `streamlit run web/app.py`
2. Select **Manual entry**
3. Click **Load example values** (optional)
4. Fill or edit the form fields
5. Click **Save form values**
6. Click **Run pipeline**

Use the optional **conflicting unstructured source** checkbox to test merge behavior across sources.

## Deploy Free on Cloud

| Platform | Cost | Best for | Setup |
| --- | --- | --- | --- |
| [Streamlit Community Cloud](https://share.streamlit.io) | Free | Easiest visual demo | Connect GitHub repo, main file: `web/app.py`, use `requirements-web.txt` |
| [Render](https://render.com) | Free tier | UI + API (sleeps after 15 min idle) | Push repo, use included `render.yaml` (deploys both services) |
| [Hugging Face Spaces](https://huggingface.co/spaces) | Free (public) | Portfolio / shareable URL | New Space → Streamlit → point to `web/app.py` |
| [Fly.io](https://fly.io) | Free allowance | Docker deploy | `fly launch` with included `Dockerfile` |

### Option A — Streamlit Cloud (recommended, ~5 minutes)

1. Push this repo to **public GitHub**
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo, branch `main`, main file path: **`web/app.py`**
4. Advanced settings → Python deps file: **`requirements-web.txt`**
5. Click **Deploy** → you get a public URL like `https://your-app.streamlit.app`

### Option B — Render (Docker)

1. Push repo to GitHub
2. [render.com](https://render.com) → **New +** → **Blueprint** → connect repo
3. Render reads `render.yaml` and builds the Docker image
4. Share the generated `*.onrender.com` URL

### Option C — Run locally with Docker

```bash
docker build -t candidate-transformer .
docker run -p 8501:8501 candidate-transformer
```

Then open `http://localhost:8501`.

**Note:** Free tiers sleep when idle (cold start ~30–60s). For internship demo video, Streamlit Cloud or Render is sufficient.

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
