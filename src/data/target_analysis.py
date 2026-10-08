from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "Dataset_Updated": ROOT / "data" / "processed" / "dataset_updated_clean.csv",
    "Augmented": ROOT / "data" / "processed" / "maternal_risk_augmented_clean.csv",
}

REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def load_data():
    data = {}

    for name, path in FILES.items():
        df = pd.read_csv(path)
        data[name] = df
        print(f"\n{name}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"Target distribution:")
        print(df["risk_level"].value_counts(dropna=False))

    return data


def target_analysis(data):
    rows = []

    for name, df in data.items():
        counts = df["risk_level"].value_counts(dropna=False)

        for risk, count in counts.items():
            rows.append({
                "dataset": name,
                "risk_level": risk,
                "count": count,
                "percentage": round(count / len(df) * 100, 2)
            })

    result = pd.DataFrame(rows)
    result.to_csv(REPORTS / "target_distribution.csv", index=False)

    print("\n=== TARGET DISTRIBUTION ===")
    print(result.to_string(index=False))

    return result


def feature_by_risk(data):
    numeric_features = [
        "age",
        "systolic_bp",
        "diastolic_bp",
        "bs",
        "body_temp",
        "heart_rate",
        "bmi",
        "hemoglobin_g_dl",
        "sleep_hours",
        "phys_activity_score",
        "stress_score",
        "diet_quality_score",
    ]

    output = []

    for name, df in data.items():
        available = [c for c in numeric_features if c in df.columns]

        grouped = (
            df.groupby("risk_level")[available]
            .mean(numeric_only=True)
            .round(3)
        )

        grouped.insert(0, "dataset", name)
        grouped.insert(1, "risk_level", grouped.index)
        grouped = grouped.reset_index(drop=True)

        output.append(grouped)

    result = pd.concat(output, ignore_index=True)
    result.to_csv(REPORTS / "feature_by_risk.csv", index=False)

    print("\n=== FEATURE MEANS BY RISK ===")
    print(result.to_string(index=False))

    return result


def common_feature_comparison(data):
    common = set(data["Dataset_Updated"].columns) & set(data["Augmented"].columns)

    common = sorted(
        c for c in common
        if c not in ["risk_level", "data_source"]
    )

    rows = []

    for feature in common:
        for name, df in data.items():
            if feature not in df.columns:
                continue

            series = pd.to_numeric(df[feature], errors="coerce")

            rows.append({
                "feature": feature,
                "dataset": name,
                "count": series.notna().sum(),
                "mean": round(series.mean(), 3),
                "median": round(series.median(), 3),
                "std": round(series.std(), 3),
                "min": round(series.min(), 3),
                "max": round(series.max(), 3),
            })

    result = pd.DataFrame(rows)
    result.to_csv(REPORTS / "common_feature_comparison.csv", index=False)

    print("\n=== COMMON FEATURE COMPARISON ===")
    print(result.to_string(index=False))

    return result


def check_label_conflicts(data):
    df1 = data["Dataset_Updated"]
    df2 = data["Augmented"]

    common_features = [
        c for c in [
            "age",
            "systolic_bp",
            "diastolic_bp",
            "bs",
            "body_temp",
            "heart_rate",
        ]
        if c in df1.columns and c in df2.columns
    ]

    if not common_features:
        print("\nNo common clinical features available for conflict analysis.")
        return

    a = df1[common_features + ["risk_level"]].copy()
    b = df2[common_features + ["risk_level"]].copy()

    for col in common_features:
        a[col] = pd.to_numeric(a[col], errors="coerce")
        b[col] = pd.to_numeric(b[col], errors="coerce")

    merged = a.merge(
        b,
        on=common_features,
        suffixes=("_dataset_a", "_dataset_b")
    )

    if merged.empty:
        print("\nNo exact matching clinical profiles found between datasets.")
        return

    conflicts = merged[
        merged["risk_level_dataset_a"] != merged["risk_level_dataset_b"]
    ]

    print("\n=== LABEL CONFLICT ANALYSIS ===")
    print(f"Exact matching clinical profiles: {len(merged)}")
    print(f"Conflicting labels: {len(conflicts)}")

    if len(merged) > 0:
        conflict_rate = len(conflicts) / len(merged) * 100
        print(f"Conflict rate: {conflict_rate:.2f}%")

    conflicts.to_csv(
        REPORTS / "label_conflicts.csv",
        index=False
    )


def main():
    print("MATERNAL RISK TARGET ANALYSIS")
    print("=" * 40)

    data = load_data()

    target_analysis(data)
    feature_by_risk(data)
    common_feature_comparison(data)
    check_label_conflicts(data)

    print("\nAnalysis completed.")
    print(f"Reports saved to: {REPORTS}")


if __name__ == "__main__":
    main()