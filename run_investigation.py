
import json

from app.agent.investigation import investigate_dataset


if __name__ == "__main__":
    result = investigate_dataset(
        "data/sample/transactions_clean.csv",
        "data/generated/transactions_corrupted.csv",
    )

    print(json.dumps(result, indent=2, default=str))
