
import json

import pandas as pd

from app.profiler.profile import profile_dataframe


def test_profile_counts_and_missing_values():
    df = pd.DataFrame({
        "amount": [100, 200, None],
        "customer": ["A", "B", "A"],
    })

    result = profile_dataframe(df)

    assert result["row_count"] == 3
    assert result["column_count"] == 2
    assert result["columns"]["amount"]["missing_count"] == 1
    assert result["columns"]["amount"]["missing_percentage"] == 33.33
    assert result["columns"]["customer"]["unique_count"] == 2


def test_empty_dataframe():
    result = profile_dataframe(pd.DataFrame())

    assert result["row_count"] == 0
    assert result["column_count"] == 0


def test_profile_is_json_serializable():
    df = pd.DataFrame({"amount": [10, 20, None]})

    json.dumps(profile_dataframe(df))


def test_duplicate_rows():
    df = pd.DataFrame({
        "id": [1, 1],
        "name": ["A", "A"],
    })

    result = profile_dataframe(df)

    assert result["duplicate_row_count"] == 1
