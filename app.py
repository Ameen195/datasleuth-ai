
from pathlib import Path
import json
import tempfile

import pandas as pd
import streamlit as st

from app.profiler.incident_report import build_incident_report
from app.agent.investigation import investigate_dataset


st.set_page_config(
    page_title="DataSleuth AI",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 DataSleuth AI")
st.subheader("Autonomous Data Incident Investigation")
st.caption(
    "Compare two CSV datasets, detect data-quality issues, "
    "and generate an evidence-grounded AI diagnosis."
)

with st.sidebar:
    st.header("About")
    st.write("Local AI-powered data quality investigation.")
    st.write("Model: Qwen 3.5 4B via Ollama")
    st.write("Analysis: Pandas + LangGraph")
    st.divider()
    st.info("Your uploaded CSV files are processed locally by this application.")

baseline_file = st.file_uploader(
    "Upload baseline CSV",
    type=["csv"],
    key="baseline",
)

current_file = st.file_uploader(
    "Upload current CSV",
    type=["csv"],
    key="current",
)

if baseline_file is not None and current_file is not None:
    try:
        baseline_df = pd.read_csv(baseline_file)
        current_df = pd.read_csv(current_file)

        st.header("Dataset overview")

        col1, col2, col3 = st.columns(3)
        col1.metric("Baseline rows", len(baseline_df))
        col2.metric("Current rows", len(current_df))
        col3.metric(
            "Columns changed",
            len(set(baseline_df.columns) ^ set(current_df.columns)),
        )

        with st.expander("Preview baseline dataset"):
            st.dataframe(baseline_df.head(20), use_container_width=True)

        with st.expander("Preview current dataset"):
            st.dataframe(current_df.head(20), use_container_width=True)

        if st.button("Run investigation", type="primary", use_container_width=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                baseline_path = Path(temp_dir) / "baseline.csv"
                current_path = Path(temp_dir) / "current.csv"

                baseline_df.to_csv(baseline_path, index=False)
                current_df.to_csv(current_path, index=False)

                st.session_state["incident_report"] = None
                st.session_state["diagnosis"] = None
                st.session_state["tool_calls_used"] = None

                try:
                    with st.spinner("Detecting anomalies and investigating with AI..."):
                        report = build_incident_report(
                            baseline_df,
                            current_df,
                        )

                        result = investigate_dataset(
                            str(baseline_path),
                            str(current_path),
                        )

                    st.session_state["incident_report"] = report
                    st.session_state["diagnosis"] = result["diagnosis"]
                    st.session_state["tool_calls_used"] = result.get(
                        "tool_calls_used", 0
                    )
                    st.session_state["evidence_summary"] = result.get(
                        "evidence_summary", ""
                    )
                    st.session_state["analysis_complete"] = True

                except Exception as exc:
                    st.session_state["analysis_complete"] = False
                    st.error(f"Investigation failed: {exc}")

        if st.session_state.get("analysis_complete"):
            report = st.session_state["incident_report"]
            diagnosis = st.session_state["diagnosis"]

            st.header("Incident summary")

            m1, m2, m3 = st.columns(3)
            m1.metric("Findings", report.get("finding_count", 0))
            m2.metric("Incident status", report.get("status", "unknown"))
            m3.metric(
                "AI tool calls",
                st.session_state.get("tool_calls_used", 0),
            )

            findings = report.get("findings", [])

            
            st.subheader("Detected findings")

            if findings:
                findings_df = pd.DataFrame(findings)

                severity_counts = (
                    findings_df["severity"]
                    .fillna("unknown")
                    .str.lower()
                    .value_counts()
                )

                chart_col, table_col = st.columns([1, 2])

                with chart_col:
                    st.markdown("#### Findings by severity")
                    st.bar_chart(severity_counts)

                with table_col:
                    st.markdown("#### Finding details")
                    st.dataframe(findings_df, use_container_width=True)

            else:
                st.success("No findings detected by the deterministic checks.")

            evidence_summary = st.session_state.get("evidence_summary", "")

            if evidence_summary:
                with st.expander("Evidence-based diagnosis", expanded=True):
                    st.markdown(evidence_summary)
            st.subheader("AI diagnosis")

            if diagnosis and diagnosis.strip():
                st.markdown(diagnosis)
            else:
                st.warning("The AI returned an empty diagnosis. "
                           "Review the deterministic findings above."
                )


            st.download_button(
                "Download incident report (JSON)",
                data=json.dumps(
                    {
                        "incident_report": report,
                        "diagnosis": diagnosis,
                        "tool_calls_used": st.session_state.get(
                            "tool_calls_used", 0
                        ),
                    },
                    indent=2,
                    default=str,
                ),
                file_name="datasleuth_incident_report.json",
                mime="application/json",
            )

            
            findings_markdown = "\n".join(
                f"- **{finding.get('anomaly_type', 'Finding')}** "
                f"({finding.get('severity', 'unknown')} severity): "
                f"{finding.get('evidence') or finding.get('column') or finding.get('key_columns') or 'See finding details'}"
                for finding in findings
            )

            markdown_report = f"""# DataSleuth AI — Incident Report

## Incident Summary

- **Incident ID:** {report.get('incident_id', 'N/A')}
- **Status:** {report.get('status', 'unknown')}
- **Baseline rows:** {report.get('baseline_rows', 'N/A')}
- **Current rows:** {report.get('current_rows', 'N/A')}
- **Total findings:** {report.get('finding_count', len(findings))}
- **AI tool calls:** {st.session_state.get('tool_calls_used', 0)}

## Detected Findings

{findings_markdown or 'No findings detected.'}

## AI Diagnosis

{diagnosis or 'No AI diagnosis available.'}

## Important Note

This report contains deterministic data-quality findings and an AI-generated diagnosis.
Verify proposed root causes and recommended actions before modifying production data.
"""

            st.download_button(
                "Download incident report (Markdown)",
                data=markdown_report,
                file_name="datasleuth_incident_report.md",
                mime="text/markdown",
            )


    except Exception as exc:
        st.error(f"Could not read the uploaded CSV files: {exc}")

else:
    st.info("Upload both a baseline CSV and a current CSV to get started.")
