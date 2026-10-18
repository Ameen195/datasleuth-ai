
from __future__ import annotations

import json
import os
from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

import pandas as pd
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import trim_messages
from langchain_core.messages import RemoveMessage
from langchain_core.messages import get_buffer_string
from langchain_core.messages import convert_to_messages
from langchain_core.messages import message_chunk_to_message
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.profiler.incident_report import build_incident_report


MAX_TOOL_CALLS = 6


class InvestigationState(TypedDict):
    baseline_path: str
    current_path: str
    report: dict
    messages: Annotated[list[AnyMessage], add_messages]
    diagnosis: str
    tool_calls_used: int


@tool
def inspect_column(
    current_path: str,
    column: str,
) -> str:
    """Inspect a column's data type, missing values, unique count and numeric statistics."""
    df = pd.read_csv(current_path)

    if column not in df.columns:
        return json.dumps({
            "error": f"Column {column!r} does not exist.",
            "available_columns": list(df.columns),
        })

    series = df[column]

    result = {
        "column": column,
        "dtype": str(series.dtype),
        "row_count": len(df),
        "missing_count": int(series.isna().sum()),
        "unique_count": int(series.nunique()),
    }

    if pd.api.types.is_numeric_dtype(series):
        result["minimum"] = (
            float(series.min()) if series.notna().any() else None
        )
        result["maximum"] = (
            float(series.max()) if series.notna().any() else None
        )
        result["mean"] = (
            float(series.mean()) if series.notna().any() else None
        )

    return json.dumps(result)


@tool
def compare_column_schema(
    baseline_path: str,
    current_path: str,
) -> str:
    """Compare baseline and current column names and data types."""
    baseline = pd.read_csv(baseline_path)
    current = pd.read_csv(current_path)

    result = {
        "baseline_columns": {
            column: str(dtype)
            for column, dtype in baseline.dtypes.items()
        },
        "current_columns": {
            column: str(dtype)
            for column, dtype in current.dtypes.items()
        },
        "added_columns": sorted(
            set(current.columns) - set(baseline.columns)
        ),
        "removed_columns": sorted(
            set(baseline.columns) - set(current.columns)
        ),
    }

    return json.dumps(result)


@tool
def get_incident_evidence(
    baseline_path: str,
    current_path: str,
) -> str:
    """Run the deterministic incident detector and return its findings."""
    baseline = pd.read_csv(baseline_path)
    current = pd.read_csv(current_path)

    report = build_incident_report(baseline, current)
    return json.dumps(report, default=str)


@tool
def inspect_duplicate_keys(
    current_path: str,
    key_column: str = "transaction_id",
) -> str:
    """Inspect duplicate key values and report the affected rows and counts."""
    df = pd.read_csv(current_path)

    if key_column not in df.columns:
        return json.dumps({
            "error": f"Key column {key_column!r} does not exist.",
            "available_columns": list(df.columns),
        })

    duplicated_mask = df[key_column].notna() & df[key_column].duplicated(
        keep=False
    )
    duplicate_rows = df.loc[duplicated_mask, [key_column]].copy()

    duplicate_value_counts = (
        df.loc[df[key_column].notna(), key_column]
        .value_counts()
    )
    duplicate_value_counts = duplicate_value_counts[
        duplicate_value_counts > 1
    ]

    return json.dumps({
        "key_column": key_column,
        "row_count": len(df),
        "duplicate_key_value_count": int(len(duplicate_value_counts)),
        "affected_row_count": int(duplicated_mask.sum()),
        "duplicate_values": [
            {
                "value": str(value),
                "occurrences": int(count),
            }
            for value, count in duplicate_value_counts.items()
        ],
        "affected_rows": [
            {
                "row_index": int(index),
                "key_value": str(row[key_column]),
            }
            for index, row in duplicate_rows.iterrows()
        ],
        "null_key_count": int(df[key_column].isna().sum()),
    })


TOOLS = [
    inspect_column,
    compare_column_schema,
    get_incident_evidence,
    inspect_duplicate_keys,
]


def _fallback_diagnosis(report: dict) -> str:
    """Build a reliable summary when the LLM returns no usable text."""
    findings = report.get("findings", [])

    if not findings:
        return (
            "No data-quality findings were reported by the deterministic "
            "incident detector. Further investigation may still be needed."
        )

    lines = [
        "DataSleuth AI investigation summary",
        "",
        f"Incident ID: {report.get('incident_id', 'N/A')}",
        f"Findings: {len(findings)}",
        "",
        "Confirmed findings from the deterministic detector:",
    ]

    for finding in findings:
        lines.append(
            f"- [{finding.get('severity', 'unknown')}] "
            f"{finding.get('type', 'finding')}: "
            f"{finding.get('column', finding.get('name', 'dataset'))}. "
            f"{json.dumps(finding, default=str)}"
        )

    lines.extend([
        "",
        "Limitations: These findings identify observed data-quality "
        "issues; they do not by themselves establish the root cause.",
        "Recommended next steps: Verify the source data, review upstream "
        "schema changes, and correct confirmed issues through an approved "
        "data-repair process. The agent has not modified the datasets.",
    ])

    return "\n".join(lines)


def build_investigation_graph():
    """Create a graph that investigates incidents with a hard tool-call limit."""

    if os.getenv("GROQ_API_KEY"):
        model = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            temperature=0,
            max_tokens=512,
        )
    else:
        model = ChatOllama(
            model="qwen3.5:4b",
            temperature=0,
            num_ctx=2048,
            num_predict=512,
            reasoning=False,
        )
    model_with_tools = model.bind_tools(TOOLS)
    tool_node = ToolNode(TOOLS)

    def investigate(state: InvestigationState) -> dict:
        response = model_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def route(state: InvestigationState) -> str:
        last_message = state["messages"][-1]
        calls = getattr(last_message, "tool_calls", None) or []

        if not calls:
            return "finalize"

        used = state.get("tool_calls_used", 0)

        if used + len(calls) > MAX_TOOL_CALLS:
            return "limit"

        return "tools"

    def execute_tools(state: InvestigationState) -> dict:
        """Execute only calls that fit within the remaining budget."""
        last_message = state["messages"][-1]
        calls = getattr(last_message, "tool_calls", None) or []
        used = state.get("tool_calls_used", 0)

        if used + len(calls) > MAX_TOOL_CALLS:
            raise RuntimeError("Tool-call limit exceeded.")

        tool_result = tool_node.invoke({"messages": [last_message]})

        return {
            "messages": tool_result["messages"],
            "tool_calls_used": used + len(calls),
        }

    def limit_reached(state: InvestigationState) -> dict:
        """Ask the model for a final answer without granting more tools."""
        response = model.invoke(
            state["messages"]
            + [
                HumanMessage(
                    content=(
                        "The investigation tool-call limit has been reached. "
                        "Do not request or execute any more tools. Summarize "
                        "only the evidence already available, distinguish "
                        "confirmed findings from hypotheses, and recommend "
                        "safe next steps."
                    )
                )
            ]
        )

        diagnosis = str(response.content).strip()

        if not diagnosis:
            diagnosis = _fallback_diagnosis(state["report"])

        return {
            "messages": [response],
            "diagnosis": diagnosis,
        }

    def finalize(state: InvestigationState) -> dict:
        last_message = state["messages"][-1]
        diagnosis = str(getattr(last_message, "content", "")).strip()

        if not diagnosis:
            diagnosis = _fallback_diagnosis(state["report"])

        return {"diagnosis": diagnosis}

    builder = StateGraph(InvestigationState)

    builder.add_node("investigate", investigate)
    builder.add_node("tools", execute_tools)
    builder.add_node("limit", limit_reached)
    builder.add_node("finalize", finalize)

    builder.add_edge(START, "investigate")

    builder.add_conditional_edges(
        "investigate",
        route,
        {
            "tools": "tools",
            "limit": "limit",
            "finalize": "finalize",
        },
    )

    builder.add_edge("tools", "investigate")
    builder.add_edge("limit", END)
    builder.add_edge("finalize", END)

    return builder.compile()
    
def build_evidence_summary(report: dict) -> str:
    """Summarize detector findings without mixing facts with hypotheses."""
    findings = report.get("findings", [])

    lines = [
        "# DataSleuth AI — Evidence Summary",
        "",
        "## Confirmed Findings",
    ]

    if not findings:
        lines.append("No anomalies were detected by the configured checks.")
    else:
        for finding in findings:
            anomaly_type = finding.get("anomaly_type", "unknown")
            severity = finding.get("severity", "unknown")
            column = finding.get("column")
            evidence = finding.get("evidence")
            key_columns = finding.get("key_columns")
            affected_rows = finding.get("affected_row_count")
            invalid_count = finding.get("invalid_count")

            details = []
            if column:
                details.append(f"column: {column}")
            if key_columns:
                details.append(f"key columns: {', '.join(key_columns)}")
            if affected_rows is not None:
                details.append(f"affected rows: {affected_rows}")
            if invalid_count is not None:
                details.append(f"invalid count: {invalid_count}")
            if evidence:
                details.append(str(evidence))

            detail_text = "; ".join(details) or "See detector finding details."
            lines.append(
                f"- **{anomaly_type}** ({severity} severity): {detail_text}"
            )

    lines.extend([
        "",
        "## Possible Explanations — Not Yet Verified",
        "- Schema changes may reflect an intentional rename or an upstream change.",
        "- Missing or invalid values may result from ingestion, transformation, "
        "or source-data issues.",
        "- Duplicate keys may result from duplicate ingestion or valid business "
        "events; confirm against the data contract.",
        "",
        "## Recommended Next Steps",
        "1. Verify each finding against source records and business rules.",
        "2. Check upstream schema and pipeline changes.",
        "3. Correct confirmed issues through an approved data-quality process.",
        "",
        "The findings above are detector results. The possible explanations "
        "are hypotheses, not established root causes.",
    ])

    return "\n".join(lines)


def investigate_dataset(
    baseline_path: str,
    current_path: str
) -> dict:
    """Run an evidence-grounded investigation of two CSV datasets."""

    baseline = pd.read_csv(baseline_path)
    current = pd.read_csv(current_path)
    report = build_incident_report(baseline, current)

    system_message = SystemMessage(
        
        content=(
            "You are DataSleuth AI, a careful data incident investigator. "
            "Use the deterministic incident report as the source of truth for "
            "detected findings. Review EVERY finding in the report; do not omit "
            "any finding, including low-severity schema changes. "
            "For each finding, state its anomaly type, affected column or key, "
            "severity, and the evidence available in the report or tool results. "
            "Do not claim a tool verified something unless a tool actually did so. "
            "Separate confirmed detector findings from hypotheses about root causes. "
            "Never invent statistics, row values, or causes. "
            "If evidence is insufficient, explicitly say so. "
            "Recommend safe next steps without modifying the data. "
            "Use these headings: Confirmed Findings, Hypotheses, "
            "Recommended Next Steps. "
            "Use tools only when they provide useful additional evidence."
        )

    )

    user_message = HumanMessage(
        content=(
            "Investigate this data incident.\n"
            f"Baseline CSV: {baseline_path}\n"
            f"Current CSV: {current_path}\n"
            "Initial deterministic report:\n"
            f"{json.dumps(report, default=str)}\n"
            "Inspect the most important findings using your tools, then "
            "explain what is confirmed and what remains uncertain."
        )
    )

    graph = build_investigation_graph()

    result = graph.invoke(
        {
            "baseline_path": baseline_path,
            "current_path": current_path,
            "report": report,
            "messages": [system_message, user_message],
            "diagnosis": "",
            "tool_calls_used": 0,
        },
        config={"recursion_limit": 20},
    )

    return {
    "incident_report": report,
    "diagnosis": result["diagnosis"],
    "evidence_summary": build_evidence_summary(report),
    "tool_calls_used": result["tool_calls_used"],
    }
