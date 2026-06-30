# Eightfold Submission — Multi-Source Candidate Data Transformer

**Candidate:** Abhinav Patel  
**Assignment:** Eightfold Engineering Intern (Jul–Dec 2026)

---

## Submission Links

| Item | Link |
| --- | --- |
| **GitHub Repository** | https://github.com/Abhinav3289/eightfold_assignment_candidate-profile_transformers- |
| **Live Web UI** | https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/ |
| **Design Document (PDF)** | Export `docs/DESIGN.md` → `Abhinav_Patel_<YourEmail>_Eightfold.pdf` |
| **Demo Video** | Upload to YouTube/Loom and add link below |

**Demo video URL:** _[Add your 2-minute screen recording link here]_

---

## What to Submit (Checklist)

### Stage 1 — Technical Design (before or with code)

- [ ] One-page PDF: `Abhinav_Patel_<YourEmail>_Eightfold.pdf`
- [ ] Source content is in `docs/DESIGN.md` (export to PDF via Word, Google Docs, or VS Code print)

### Stage 2 — Implementation

- [x] Public GitHub repo with source code
- [x] README with run instructions
- [x] Sample outputs in `output/default_profile.json` and `output/custom_profile.json`
- [x] Tests in `tests/` (run `pytest -q`)
- [ ] ~2 minute demo video showing:
  - [ ] Live app or CLI end-to-end on sample inputs
  - [ ] Default canonical output
  - [ ] Custom projection config output
  - [ ] One design decision (structured > unstructured merge)
  - [ ] One edge case (invalid phone → omitted/null)

---

## Demo Video Script (~2 minutes)

**0:00–0:20 — Intro**  
Open live URL → explain problem: merge CSV, ATS JSON, GitHub, resume, notes into one profile.

**0:20–0:50 — Default run**  
Select **Use sample data** → **Run pipeline** → show JSON tab (name, email, E.164 phone, skills, provenance, confidence).

**0:50–1:20 — Custom config**  
Switch to **Custom projection config** → run again → show `primary_email`, `phone`, flattened `skills`.

**1:20–1:50 — Design + edge case**  
Explain: structured sources win conflicts; invalid/garbage data becomes null (never invented). Mention phone normalization and skill canonicalization.

**1:50–2:00 — Close**  
Show GitHub repo link and tests (`pytest -q`).

---

## How Reviewers Can Verify

```bash
git clone https://github.com/Abhinav3289/eightfold_assignment_candidate-profile_transformers-.git
cd eightfold_assignment_candidate-profile_transformers-
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
python -m candidate_transformer data/samples/recruiter.csv data/samples/ats.json data/samples/github_profile.json data/samples/resume.txt data/samples/recruiter_notes.txt -o output/default_profile.json
```

Or use the live app — no install required.

---

## Assumptions & Descoped (for evaluators)

- GitHub live API optional; sample JSON used for deterministic demos
- LinkedIn scraping not implemented (ToS); links from ATS/notes only
- Resume parsing is heuristic, not ML-based
- Single-candidate merge per run (batch wrapper not implemented)
- Location parsing is rule-based, not geocoded

---

## Email Submission Template

```
Subject: Eightfold Engineering Intern Assignment — Abhinav Patel

Hi,

Please find my submission for the Multi-Source Candidate Data Transformer assignment:

GitHub: https://github.com/Abhinav3289/eightfold_assignment_candidate-profile_transformers-
Live Demo: https://abhinav3289-eightfold-assignment-candidate-profil-webapp-nghud3.streamlit.app/
Design Doc: Abhinav_Patel_<YourEmail>_Eightfold.pdf (attached)
Demo Video: <your-video-link>

Thank you,
Abhinav Patel
```
