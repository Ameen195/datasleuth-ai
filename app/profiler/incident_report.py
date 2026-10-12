
from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd

from app.profiler.anomalies import (
    detect_duplicate_keys,
    detect_invalid_values,
)
from app.profiler.comparison import compare_dataset_runs


def build_incident_report(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
) -> dict:
    """Combine schema and data-quality findings into one report."""

    findings = compare_dataset_runs(baseline, current)

    findings.extend(
        detect_duplicate_keys(current, ["transaction_id"])
        if "transaction_id" in current.columns
        else []
    )

    findings.extend(
        detect_invalid_values(
            current,
            {
                "transaction_date": {"not_null": True},
                "amount": {"min": 0, "max": 500},
            },
        )
    )

    for finding in findings:
        finding.setdefault("severity", "medium")

    severity_order = {"high": 3, "medium": 2, "low": 1}
    findings.sort(
        key=lambda item: severity_order.get(item["severity"], 0),
        reverse=True,
    )

    return {
        "incident_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "investigated" if findings else "no_anomalies",
        "baseline_rows": len(baseline),
        "current_rows": len(current),
        "finding_count": len(findings),
        "findings": findings,
    }
