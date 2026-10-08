from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data" / "processed" / "dataset_updated_clean.csv"
OUTPUT = ROOT / "data" / "processed" / "baseline_dataset.csv"

FEATURES = [
    "age",
    "systolic_bp",
    "diastolic",
    "bs",
    "body_temp",
    "bmi",
    "previous_complications",
    "preexisting_diabetes",
    "gestational_diabetes",
    "mental_health",
    "heart_rate",
]

TARGET = "risk_level"


def main():
    df = pd.read_csv(INPUT)

    df = df[FEATURES + [TARGET]].copy()

    df = df.dropna(subset=[TARGET])

    df[TARGET] = (
        df[TARGET]
        .astype(str)
        .str.strip()
        .str.title()
    )

    df = df[df[TARGET].isin(["Low", "High"])]

    df = df.drop_duplicates()

    df.to_csv(OUTPUT, index=False)

    print("BASELINE DATASET CREATED")
    print("=" * 40)
    print(f"Rows: {len(df)}")
    print(f"Features: {len(FEATURES)}")
    print(f"Missing values: {df.isna().sum().sum()}")

    print("\nTarget distribution:")
    print(df[TARGET].value_counts())

    print("\nTarget percentage:")
    print((df[TARGET].value_counts(normalize=True) * 100).round(2))

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()