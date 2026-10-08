from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "Dataset_Updated": ROOT / "data" / "processed" / "dataset_updated_clean.csv",
    "Augmented": ROOT / "data" / "processed" / "maternal_risk_augmented_clean.csv",
}

REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def analyze_dataset(name, path):
    df = pd.read_csv(path)

    target = df["risk_level"].dropna()

    print(f"\n{'=' * 50}")
    print(name)
    print(f"{'=' * 50}")

    print(f"Rows: {len(df)}")
    print(f"Features: {len(df.columns) - 2}")
    print(f"Missing values: {df.isna().sum().sum()}")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\nTarget:")
    print(target.value_counts())
    print("\nTarget percentage:")
    print((target.value_counts(normalize=True) * 100).round(2))

    print("\nNumeric feature statistics:")
    numeric = df.select_dtypes(include="number")

    stats = numeric.describe().T[
        ["count", "mean", "std", "min", "max"]
    ].round(3)

    print(stats.to_string())

    return {
        "dataset": name,
        "rows": len(df),
        "features": len(df.columns) - 2,
        "missing_values": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "target_classes": target.nunique(),
        "target_distribution": "; ".join(
            f"{k}: {v}" for k, v in target.value_counts().items()
        ),
    }


def compare_features(data):
    results = []

    for name, path in FILES.items():
        df = pd.read_csv(path)

        numeric = df.select_dtypes(include="number")

        for feature in numeric.columns:
            if feature == "risk_level":
                continue

            results.append({
                "dataset": name,
                "feature": feature,
                "missing": int(df[feature].isna().sum()),
                "mean": round(df[feature].mean(), 3),
                "std": round(df[feature].std(), 3),
                "min": round(df[feature].min(), 3),
                "max": round(df[feature].max(), 3),
            })

    result = pd.DataFrame(results)
    result.to_csv(
        REPORTS / "dataset_feature_statistics.csv",
        index=False
    )


def main():
    print("BASELINE DATASET SELECTION ANALYSIS")

    results = []

    for name, path in FILES.items():
        results.append(analyze_dataset(name, path))

    summary = pd.DataFrame(results)

    summary.to_csv(
        REPORTS / "dataset_selection_summary.csv",
        index=False
    )

    compare_features(summary)

    print("\n" + "=" * 50)
    print("DATASET SELECTION ANALYSIS COMPLETED")
    print("=" * 50)

    print("\nGenerated:")
    print("reports/dataset_selection_summary.csv")
    print("reports/dataset_feature_statistics.csv")


if __name__ == "__main__":
    main()