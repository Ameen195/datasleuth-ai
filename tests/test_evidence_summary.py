
from app.agent.investigation import build_evidence_summary


def test_evidence_summary_includes_all_findings():
    report = {
        "finding_count": 2,
        "findings": [
            {
                "anomaly_type": "null_values",
                "severity": "high",
                "column": "transaction_date",
                "invalid_count": 1,
            },
            {
                "anomaly_type": "duplicate_keys",
                "severity": "high",
                "key_columns": ["transaction_id"],
                "affected_row_count": 2,
            },
        ],
    }

    summary = build_evidence_summary(report)

    assert "null_values" in summary
    assert "transaction_date" in summary
    assert "duplicate_keys" in summary
    assert "transaction_id" in summary
    assert "Possible Explanations" in summary


def test_evidence_summary_handles_clean_dataset():
    report = {
        "finding_count": 0,
        "findings": [],
    }

    summary = build_evidence_summary(report)

    assert "No anomalies were detected" in summary
    assert "Possible Explanations" in summary


def test_evidence_summary_covers_all_known_defect_types():
    report = {
        "finding_count": 5,
        "findings": [
            {
                "anomaly_type": "removed_column",
                "severity": "high",
                "column": "payment_method",
                "evidence": "Column is missing from current data.",
            },
            {
                "anomaly_type": "duplicate_keys",
                "severity": "high",
                "key_columns": ["transaction_id"],
                "affected_row_count": 2,
            },
            {
                "anomaly_type": "null_values",
                "severity": "high",
                "column": "transaction_date",
                "invalid_count": 1,
            },
            {
                "anomaly_type": "invalid_numeric_values",
                "severity": "high",
                "column": "amount",
                "invalid_count": 1,
            },
            {
                "anomaly_type": "added_column",
                "severity": "low",
                "column": "payment_type",
                "evidence": "Column did not exist in baseline.",
            },
        ],
    }

    summary = build_evidence_summary(report)

    for defect in [
        "removed_column",
        "duplicate_keys",
        "null_values",
        "invalid_numeric_values",
        "added_column",
    ]:
        assert defect in summary
