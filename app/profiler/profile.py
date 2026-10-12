import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Generate a JSON-serializable data-quality profile."""

    columns = {}

    for name in df.columns:
        series = df[name]

        column_info = {
            "data_type": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": (
                round(float(series.isna().mean() * 100), 2)
                if len(df) else 0.0
            ),
            "unique_count": int(series.nunique()),
        }

        if pd.api.types.is_numeric_dtype(series):
            column_info["statistics"] = {
                "min": float(series.min()) if series.notna().any() else None,
                "max": float(series.max()) if series.notna().any() else None,
                "mean": float(series.mean()) if series.notna().any() else None,
                "std": float(series.std()) if series.notna().any() else None,
            }

        columns[str(name)] = column_info

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": columns,
        "duplicate_row_count": int(df.duplicated().sum()),
    }
