
import pandas as pd

from app.profiler.incident_report import build_incident_report


def test_incident_report_detects_known_defects():
    baseline = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3"],
        "transaction_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "amount": [100.0, 200.0, 300.0],
        "payment_method": ["UPI", "Card", "Cash"],
    })

    current = pd.DataFrame({
        "transaction_id": ["T1", "T1", "T3"],
        "transaction_date": ["2026-01-01", None, "2026-01-03"],
        "amount": [100.0, -50.0, 300.0],
        "payment_type": ["UPI", "Card", "Cash"],
    })

    report = build_incident_report(baseline, current)
    kinds = {item["anomaly_type"] for item in report["findings"]}

    assert report["baseline_rows"] == 3
    assert report["current_rows"] == 3
    assert report["finding_count"] == len(report["findings"])
    assert report["incident_id"]
    assert report["created_at"]

    assert {
        "removed_column",
        "added_column",
        "duplicate_keys",
        "null_values",
        "invalid_numeric_values",
    }.issubset(kinds)


def test_clean_dataset_has_no_findings():
    clean = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "transaction_date": ["2026-01-01", "2026-01-02"],
        "amount": [100.0, 200.0],
        "payment_method": ["UPI", "Card"],
    })

    report = build_incident_report(clean.copy(), clean.copy())

    assert report["finding_count"] == 0
    assert report["status"] == "no_anomalies"
