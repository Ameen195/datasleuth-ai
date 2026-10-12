
import pandas as pd


def detect_missing_values(
    df: pd.DataFrame,
    threshold: float = 10.0,
) -> list[dict]:
    """Detect columns exceeding the missing-value percentage threshold."""
    if not 0 <= threshold <= 100:
        raise ValueError("threshold must be between 0 and 100")

    findings = []

    for column in df.columns:
        count = int(df[column].isna().sum())
        percentage = float(df[column].isna().mean() * 100) if len(df) else 0.0

        if percentage > threshold:
            findings.append({
                "anomaly_type": "missing_values",
                "severity": "high" if percentage >= 30 else "medium",
                "column": str(column),
                "missing_count": count,
                "missing_percentage": round(percentage, 2),
                "threshold": threshold,
            })

    return findings


def detect_duplicate_rows(df: pd.DataFrame) -> list[dict]:
    """Detect complete duplicate rows."""
    count = int(df.duplicated().sum())

    if count == 0:
        return []

    return [{
        "anomaly_type": "duplicate_rows",
        "severity": "medium",
        "duplicate_count": count,
    }]


def detect_numeric_out_of_bounds(
    df: pd.DataFrame,
    bounds: dict[str, tuple[float, float]],
) -> list[dict]:
    """Detect numeric values outside configured inclusive bounds."""
    findings = []

    for column, (minimum, maximum) in bounds.items():
        if minimum > maximum:
            raise ValueError(f"Invalid bounds for {column}")

        if column not in df.columns:
            continue

        numeric = pd.to_numeric(df[column], errors="coerce")
        invalid = numeric.notna() & ((numeric < minimum) | (numeric > maximum))
        count = int(invalid.sum())

        if count:
            findings.append({
                "anomaly_type": "numeric_out_of_bounds",
                "severity": "high",
                "column": column,
                "invalid_count": count,
                "minimum_allowed": minimum,
                "maximum_allowed": maximum,
            })

    return findings


def compare_schemas(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
) -> list[dict]:
    """Identify added, removed, and type-changed columns."""
    findings = []
    old_columns = set(baseline.columns)
    new_columns = set(current.columns)

    for column in sorted(new_columns - old_columns):
        findings.append({
            "anomaly_type": "added_column",
            "column": str(column),
        })

    for column in sorted(old_columns - new_columns):
        findings.append({
            "anomaly_type": "removed_column",
            "column": str(column),
        })

    for column in sorted(old_columns & new_columns):
        old_type = str(baseline[column].dtype)
        new_type = str(current[column].dtype)

        if old_type != new_type:
            findings.append({
                "anomaly_type": "type_changed",
                "column": str(column),
                "baseline_type": old_type,
                "current_type": new_type,
            })

    return findings


def detect_duplicate_keys(
    df: pd.DataFrame,
    key_columns: list[str],
) -> list[dict]:
    """Detect rows sharing duplicate values in configured key columns."""
    missing = [column for column in key_columns if column not in df.columns]

    if missing:
        raise ValueError(f"Missing key columns: {missing}")

    count = int(df.duplicated(subset=key_columns, keep=False).sum())

    if count == 0:
        return []

    return [{
        "anomaly_type": "duplicate_keys",
        "severity": "high",
        "key_columns": key_columns,
        "affected_row_count": count,
    }]


def detect_invalid_values(
    df: pd.DataFrame,
    rules: dict[str, dict],
) -> list[dict]:
    """Detect null values and numeric values violating configured rules."""
    findings = []

    for column, rule in rules.items():
        if column not in df.columns:
            findings.append({
                "anomaly_type": "missing_required_column",
                "severity": "high",
                "column": column,
            })
            continue

        series = df[column]

        if rule.get("not_null", False):
            count = int(series.isna().sum())
            if count:
                findings.append({
                    "anomaly_type": "null_values",
                    "severity": "high",
                    "column": column,
                    "invalid_count": count,
                })

        if "min" in rule or "max" in rule:
            numeric = pd.to_numeric(series, errors="coerce")
            invalid = numeric.isna() & series.notna()

            if "min" in rule:
                invalid |= numeric < rule["min"]
            if "max" in rule:
                invalid |= numeric > rule["max"]

            count = int(invalid.sum())
            if count:
                findings.append({
                    "anomaly_type": "invalid_numeric_values",
                    "severity": "high",
                    "column": column,
                    "invalid_count": count,
                    "minimum_allowed": rule.get("min"),
                    "maximum_allowed": rule.get("max"),
                })

    return findings
