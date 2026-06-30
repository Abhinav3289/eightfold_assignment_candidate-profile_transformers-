"""Streamlit web UI for the candidate transformer pipeline."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from candidate_transformer.ingest import ingest_manual_form
from candidate_transformer.models import OutputConfig
from candidate_transformer.pipeline import load_output_config, run_pipeline
SAMPLES = ROOT / "data" / "samples"
DEFAULT_CONFIG = ROOT / "config" / "custom_output.json"

MANUAL_DEFAULTS: dict[str, Any] = {
    "full_name": "Abhinav Patel",
    "email": "abhinav.patel@example.com",
    "phone": "+91 98765 43210",
    "headline": "B.Tech CSE Student | Aspiring Software Engineer",
    "years_experience": 1.0,
    "city": "Bhopal",
    "region": "Madhya Pradesh",
    "country": "IN",
    "linkedin": "https://linkedin.com/in/abhinav-patel-iiit",
    "github": "https://github.com/abhinav3289",
    "portfolio": "https://abhinavpatel.dev",
    "skills": "Python, Java, JavaScript, React, SQL, Django",
    "company": "TechNova Solutions",
    "title": "Software Engineering Intern",
    "start_date": "May 2025",
    "end_date": "Jul 2025",
    "summary": "Built REST APIs and internal dashboards using Python and React.",
    "institution": "IIIT Bhopal",
    "degree": "B.Tech",
    "field": "Computer Science and Engineering",
    "end_year": 2026,
    "notes": "Promising fresher from IIIT Bhopal. Strong Python and DSA fundamentals.",
    "note_skills": "Python, Java",
}


def build_output_config(
    output_mode: str,
    include_provenance: bool,
    include_confidence: bool,
) -> OutputConfig | None:
    if output_mode == "Custom projection config" and DEFAULT_CONFIG.exists():
        config = load_output_config(DEFAULT_CONFIG)
        config.include_provenance = include_provenance
        config.include_confidence = include_confidence
        return config
    return OutputConfig(
        fields=[],
        include_provenance=include_provenance,
        include_confidence=include_confidence,
    )


def render_results(result: dict[str, Any]) -> None:
    st.success("Pipeline completed successfully.")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Candidate", result.get("full_name") or result.get("candidate_id", "—"))
    emails = result.get("emails")
    metric_cols[1].metric("Emails", len(emails) if isinstance(emails, list) else (1 if result.get("primary_email") else 0))
    skills = result.get("skills", [])
    metric_cols[2].metric("Skills", len(skills))
    metric_cols[3].metric("Confidence", result.get("overall_confidence", "—"))

    tab_json, tab_provenance, tab_skills = st.tabs(["JSON output", "Provenance", "Skills"])

    with tab_json:
        st.json(result)
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="candidate_profile.json",
            mime="application/json",
        )

    with tab_provenance:
        provenance = result.get("provenance", [])
        if provenance:
            st.dataframe(provenance, use_container_width=True)
        else:
            st.write("No provenance in this output mode.")

    with tab_skills:
        if skills and isinstance(skills[0], dict):
            st.dataframe(skills, use_container_width=True)
        elif skills:
            st.write(", ".join(str(item) for item in skills))
        else:
            st.write("No skills extracted.")


st.set_page_config(
    page_title="Candidate Data Transformer",
    page_icon="🧩",
    layout="wide",
)

st.title("Multi-Source Candidate Data Transformer")
st.caption(
    "Test the pipeline using sample files, uploaded files, or manual form entry."
)

input_mode = st.radio(
    "How do you want to provide input?",
    options=["Manual entry", "Upload files", "Use sample data"],
    horizontal=True,
)

uploaded_files: list[Path] = []
manual_records = []
manual_payload: dict[str, Any] | None = None

if input_mode == "Use sample data":
    sample_paths = [
        SAMPLES / "recruiter.csv",
        SAMPLES / "ats.json",
        SAMPLES / "github_profile.json",
        SAMPLES / "resume.txt",
        SAMPLES / "recruiter_notes.txt",
    ]
    uploaded_files = [path for path in sample_paths if path.exists()]
    st.info(f"Using {len(uploaded_files)} bundled files from `data/samples/`.")

elif input_mode == "Upload files":
    files = st.file_uploader(
        "Upload source files",
        type=["csv", "json", "txt", "pdf", "docx"],
        accept_multiple_files=True,
        help="Upload at least one structured file (CSV/JSON) and one unstructured file (resume/notes).",
    )
    if files:
        temp_dir = Path(tempfile.mkdtemp(prefix="candidate_upload_"))
        for uploaded in files:
            dest = temp_dir / uploaded.name
            dest.write_bytes(uploaded.getbuffer())
            uploaded_files.append(dest)
        st.success(f"{len(uploaded_files)} file(s) ready to process.")
    else:
        st.warning("Upload one or more files to run the pipeline.")

else:
    st.subheader("Enter candidate information manually")
    st.write("Fill the form below to simulate recruiter/ATS input without uploading files.")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Load example values"):
            st.session_state["manual_form"] = MANUAL_DEFAULTS.copy()
        if st.button("Clear form"):
            st.session_state["manual_form"] = {}

    defaults = st.session_state.get("manual_form", MANUAL_DEFAULTS)

    with st.form("manual_candidate_form", clear_on_submit=False):
        st.markdown("**Basic info**")
        c1, c2, c3 = st.columns(3)
        full_name = c1.text_input("Full name", value=defaults.get("full_name", ""))
        email = c2.text_input("Email", value=defaults.get("email", ""))
        phone = c3.text_input("Phone", value=defaults.get("phone", ""))

        c4, c5 = st.columns(2)
        headline = c4.text_input("Headline / current title", value=defaults.get("headline", ""))
        years_experience = c5.number_input(
            "Years of experience",
            min_value=0.0,
            max_value=50.0,
            value=float(defaults.get("years_experience", 0.0) or 0.0),
            step=0.5,
        )

        st.markdown("**Location**")
        l1, l2, l3 = st.columns(3)
        city = l1.text_input("City", value=defaults.get("city", ""))
        region = l2.text_input("Region / state", value=defaults.get("region", ""))
        country = l3.text_input("Country (ISO-2, e.g. US)", value=defaults.get("country", ""))

        st.markdown("**Links**")
        k1, k2, k3 = st.columns(3)
        linkedin = k1.text_input("LinkedIn URL", value=defaults.get("linkedin", ""))
        github = k2.text_input("GitHub URL", value=defaults.get("github", ""))
        portfolio = k3.text_input("Portfolio URL", value=defaults.get("portfolio", ""))

        st.markdown("**Skills & experience**")
        skills = st.text_input(
            "Skills (comma-separated)",
            value=defaults.get("skills", ""),
            help="Example: Python, AWS, Kubernetes",
        )

        e1, e2, e3, e4 = st.columns(4)
        company = e1.text_input("Company", value=defaults.get("company", ""))
        title = e2.text_input("Job title", value=defaults.get("title", ""))
        start_date = e3.text_input("Start date", value=defaults.get("start_date", ""), placeholder="Jan 2021")
        end_date = e4.text_input("End date", value=defaults.get("end_date", ""), placeholder="Present")

        summary = st.text_area("Experience summary", value=defaults.get("summary", ""))

        st.markdown("**Education**")
        d1, d2, d3, d4 = st.columns(4)
        institution = d1.text_input("Institution", value=defaults.get("institution", ""))
        degree = d2.text_input("Degree", value=defaults.get("degree", ""))
        field = d3.text_input("Field of study", value=defaults.get("field", ""))
        end_year = d4.number_input(
            "Graduation year",
            min_value=1950,
            max_value=2035,
            value=int(defaults.get("end_year", 2020) or 2020),
            step=1,
        )

        st.markdown("**Optional second source (recruiter notes)**")
        notes = st.text_area(
            "Free-form notes",
            value=defaults.get("notes", ""),
            help="Simulates unstructured recruiter notes for merge testing.",
        )
        note_skills = st.text_input(
            "Skills mentioned in notes",
            value=defaults.get("note_skills", ""),
        )

        add_second_source = st.checkbox(
            "Also add a conflicting unstructured source (for merge testing)",
            value=False,
            help="Adds a second manual source with slightly different title/skills.",
        )

        submitted = st.form_submit_button("Save form values", use_container_width=True)

        if submitted:
            manual_payload = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "headline": headline,
                "years_experience": years_experience,
                "city": city,
                "region": region,
                "country": country,
                "linkedin": linkedin,
                "github": github,
                "portfolio": portfolio,
                "skills": skills,
                "company": company,
                "title": title,
                "start_date": start_date,
                "end_date": end_date,
                "summary": summary,
                "institution": institution,
                "degree": degree,
                "field": field,
                "end_year": end_year,
                "notes": notes,
                "note_skills": note_skills,
            }
            st.session_state["manual_form"] = manual_payload
            st.session_state["add_second_source"] = add_second_source
            st.success("Form saved. Click **Run pipeline** below to process.")

    if "manual_form" in st.session_state and st.session_state["manual_form"]:
        manual_payload = st.session_state["manual_form"]
        preview = {key: value for key, value in manual_payload.items() if value not in (None, "", [])}
        with st.expander("Preview saved manual input"):
            st.json(preview)

st.divider()

col_left, col_right = st.columns([1, 1])
with col_left:
    st.subheader("Pipeline")
with col_right:
    output_mode = st.radio(
        "Output schema",
        options=["Default canonical profile", "Custom projection config"],
        horizontal=True,
    )
    include_provenance = st.checkbox("Include provenance", value=True)
    include_confidence = st.checkbox("Include confidence", value=True)

run = st.button("Run pipeline", type="primary", use_container_width=True)

if run:
    try:
        output_config = build_output_config(output_mode, include_provenance, include_confidence)
        source_records = []

        if input_mode == "Manual entry":
            payload = st.session_state.get("manual_form")
            if not payload:
                st.error("Fill the manual form and click **Save form values** first.")
                st.stop()

            source_records.append(
                ingest_manual_form(payload, source_id="manual_structured", structured=True)
            )
            if payload.get("notes") or payload.get("note_skills"):
                source_records.append(
                    ingest_manual_form(payload, source_id="manual_notes", structured=False)
                )
            if st.session_state.get("add_second_source"):
                conflict = payload.copy()
                conflict["headline"] = "Staff Software Engineer"
                conflict["skills"] = "Python, Go, Docker"
                conflict["notes"] = "Potential staff-level candidate."
                source_records.append(
                    ingest_manual_form(conflict, source_id="manual_conflict", structured=False)
                )
        elif not uploaded_files:
            st.error("No input available. Upload files, use sample data, or save the manual form.")
            st.stop()

        with st.spinner("Running detect → ingest → normalize → merge → project → validate..."):
            result = run_pipeline(
                input_paths=uploaded_files if input_mode != "Manual entry" else None,
                source_records=source_records if input_mode == "Manual entry" else None,
                output_config=output_config,
            )

        render_results(result)

    except Exception as exc:
        st.error(f"Pipeline failed: {exc}")
