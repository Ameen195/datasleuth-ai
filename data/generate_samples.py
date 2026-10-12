
from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

SAMPLE_DIR = ROOT / "sample"
GENERATED_DIR = ROOT / "generated"


def generate_samples() -> None:
    """Create reproducible clean and deliberately corrupted datasets."""
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    rows = 100

    clean = pd.DataFrame({
        "transaction_id": [f"T{i:04d}" for i in range(1, rows + 1)],
        "customer_id": [f"C{n:03d}" for n in rng.integers(1, 31, rows)],
        "transaction_date": pd.date_range(
            "2026-01-01", periods=rows, freq="D"
        ).astype(str),
        "amount": rng.uniform(10, 500, rows).round(2),
        "payment_method": rng.choice(
            ["UPI", "Card", "Cash"], size=rows
        ),
    })

    clean_path = SAMPLE_DIR / "transactions_clean.csv"
    clean.to_csv(clean_path, index=False)

    corrupted = clean.copy()

    # Inject a duplicate transaction ID.
    corrupted.loc[1, "transaction_id"] = corrupted.loc[0, "transaction_id"]

    # Inject a missing date.
    corrupted.loc[2, "transaction_date"] = None

    # Inject an invalid amount.
    corrupted.loc[3, "amount"] = -50.0

    # Rename a column to simulate schema drift.
    corrupted = corrupted.rename(
        columns={"payment_method": "payment_type"}
    )

    corrupted_path = GENERATED_DIR / "transactions_corrupted.csv"
    corrupted.to_csv(corrupted_path, index=False)

    defects = {
        "duplicate_transaction_id": {
            "rows": [0, 1],
            "column": "transaction_id",
        },
        "missing_date": {
            "row": 2,
            "column": "transaction_date",
        },
        "invalid_amount": {
            "row": 3,
            "column": "amount",
            "value": -50.0,
        },
        "renamed_column": {
            "original": "payment_method",
            "replacement": "payment_type",
        },
    }

    defects_path = GENERATED_DIR / "known_defects.json"
    defects_path.write_text(
        json.dumps(defects, indent=2),
        encoding="utf-8",
    )

    print(f"Clean dataset: {clean_path}")
    print(f"Corrupted dataset: {corrupted_path}")
    print(f"Known defects: {defects_path}")


if __name__ == "__main__":
    generate_samples()
