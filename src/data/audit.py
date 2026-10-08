from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def clean_columns(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def audit_dataset(path):
    df = pd.read_csv(path)
    original_columns = list(df.columns)
    df = clean_columns(df)

    target_candidates = [
        "risklevel",
        "risk_level",
        "risk",
        "risk_category",
        "riskcategory"
    ]

    target = next(
        (col for col in target_candidates if col in df.columns),
        None
    )

    numeric_columns = df.select_dtypes(include="number").columns

    report = {
        "file": path.name,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "original_columns": original_columns,
        "standardized_columns": list(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_total": int(df.isna().sum().sum()),
        "missing_by_column": {
            col: int(value)
            for col, value in df.isna().sum().items()
            if value > 0
        },
        "numeric_ranges": {
            col: {
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }
            for col in numeric_columns
            if df[col].notna().any()
        },
        "target_column": target,
        "target_distribution": (
            df[target]
            .value_counts(dropna=False)
            .astype(int)
            .to_dict()
            if target
            else {}
        )
    }

    return df, report


def main():
    files = sorted(RAW_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No CSV files found in: {RAW_DIR}"
        )

    all_reports = []
    datasets = {}

    for path in files:
        print(f"\nAuditing: {path.name}")

        df, report = audit_dataset(path)

        datasets[path.name] = df
        all_reports.append(report)

        print(f"Rows: {report['rows']}")
        print(f"Columns: {report['columns']}")
        print(f"Duplicates: {report['duplicate_rows']}")
        print(f"Missing values: {report['missing_total']}")
        print(f"Target: {report['target_column']}")

        if report["target_distribution"]:
            print("Target distribution:")
            for label, count in report["target_distribution"].items():
                print(f"  {label}: {count}")

    common_columns = None

    for df in datasets.values():
        columns = set(df.columns)
        common_columns = columns if common_columns is None else common_columns & columns

    common_columns = sorted(common_columns)

    summary = {
        "datasets": all_reports,
        "common_columns": common_columns,
        "number_of_datasets": len(datasets)
    }

    with open(REPORT_DIR / "dataset_audit.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    pd.DataFrame([
        {
            "dataset": report["file"],
            "rows": report["rows"],
            "columns": report["columns"],
            "duplicates": report["duplicate_rows"],
            "missing_values": report["missing_total"],
            "target": report["target_column"]
        }
        for report in all_reports
    ]).to_csv(
        REPORT_DIR / "dataset_summary.csv",
        index=False
    )

    pd.DataFrame({
        "common_column": common_columns
    }).to_csv(
        REPORT_DIR / "common_columns.csv",
        index=False
    )

    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)

    print(f"\nDatasets found: {len(datasets)}")

    print("\nCommon columns:")
    for column in common_columns:
        print(f"  - {column}")

    print("\nReports created:")
    print(f"  {REPORT_DIR / 'dataset_audit.json'}")
    print(f"  {REPORT_DIR / 'dataset_summary.csv'}")
    print(f"  {REPORT_DIR / 'common_columns.csv'}")


if __name__ == "__main__":
    main()