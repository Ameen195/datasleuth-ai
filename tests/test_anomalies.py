
import pandas as pd

from app.profiler.anomalies import (
    compare_schemas,
    detect_duplicate_rows,
    detect_missing_values,
    detect_numeric_out_of_bounds,
)


def test_missing_values_detected():
    df = pd.DataFrame({"amount": [100, None, 200, 300]})

    findings = detect_missing_values(df, threshold=10)

    assert len(findings) == 1
    assert findings[0]["missing_count"] == 1


def test_duplicate_rows_detected():
    df = pd.DataFrame({"id": [1, 1], "name": ["A", "A"]})

    findings = detect_duplicate_rows(df)

    assert len(findings) == 1
    assert findings[0]["duplicate_count"] == 1


def test_numeric_bounds_detected():
    df = pd.DataFrame({"amount": [100, -50, 200]})

    findings = detect_numeric_out_of_bounds(
        df, {"amount": (0, 500)}
    )

    assert len(findings) == 1
    assert findings[0]["invalid_count"] == 1


def test_schema_changes_detected():
    baseline = pd.DataFrame({"id": [1], "amount": [100]})
    current = pd.DataFrame({"id": ["1"], "payment": ["UPI"]})

    findings = compare_schemas(baseline, current)
    kinds = {item["anomaly_type"] for item in findings}

    assert kinds == {"added_column", "removed_column", "type_changed"}
