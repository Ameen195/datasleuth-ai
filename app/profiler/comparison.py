
from __future__ import annotations

import pandas as pd


def compare_dataset_runs(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    missing_increase_threshold: float = 10.0,
) -> list[dict]:
    """Compare two dataset runs and return structured findings."""

    if not 0 <= missing_increase_threshold <= 100:
        raise ValueError("Threshold must be between 0 and 100")

    findings = []

    baseline_columns = set(baseline.columns)
    current_columns = set(current.columns)

    # Detect added columns.
    for column in sorted(current_columns - baseline_columns):
        findings.append({
            "anomaly_type": "added_column",
            "severity": "low",
            "column": str(column),
            "evidence": f"Column {column!r} did not exist in baseline.",
        })

    # Detect removed columns.
    for column in sorted(baseline_columns - current_columns):
        findings.append({
            "anomaly_type": "removed_column",
            "severity": "high",
            "column": str(column),
            "evidence": f"Column {column!r} is missing from current data.",
        })

    # Compare common columns.
    for column in sorted(baseline_columns & current_columns):
        old = baseline[column]
        new = current[column]

        if old.dtype != new.dtype:
            findings.append({
                "anomaly_type": "type_changed",
                "severity": "medium",
                "column": str(column),
                "baseline_type": str(old.dtype),
                "current_type": str(new.dtype),
            })

        old_missing = float(old.isna().mean() * 100) if len(old) else 0.0
        new_missing = float(new.isna().mean() * 100) if len(new) else 0.0
        increase = new_missing - old_missing

        if increase > missing_increase_threshold:
            findings.append({
                "anomaly_type": "missing_value_increase",
                "severity": "high" if increase >= 30 else "medium",
                "column": str(column),
                "baseline_missing_percentage": round(old_missing, 2),
                "current_missing_percentage": round(new_missing, 2),
                "increase_percentage_points": round(increase, 2),
                "threshold": missing_increase_threshold,
            })

    # Check duplicate rows in the current run.
    duplicate_count = int(current.duplicated().sum())

    if duplicate_count:
        findings.append({
            "anomaly_type": "duplicate_rows",
            "severity": "medium",
            "duplicate_count": duplicate_count,
        })

    return findings
