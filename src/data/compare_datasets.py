from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def standardize_columns(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def load_dataset(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_csv(path)
    return standardize_columns(df)


def column_summary(df, dataset_name):
    rows = []

    for column in df.columns:
        series = df[column]

        row = {
            "dataset": dataset_name,
            "column": column,
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "unique_values": int(series.nunique(dropna=True)),
        }

        if pd.api.types.is_numeric_dtype(series):
            row["min"] = series.min()
            row["max"] = series.max()
            row["mean"] = series.mean()
        else:
            row["min"] = None
            row["max"] = None
            row["mean"] = None

        rows.append(row)

    return rows


def value_summary(df, dataset_name):
    rows = []

    for column in df.columns:
        series = df[column]

        if series.nunique(dropna=True) <= 15:
            counts = series.value_counts(dropna=False)

            for value, count in counts.items():
                rows.append({
                    "dataset": dataset_name,
                    "column": column,
                    "value": str(value),
                    "count": int(count)
                })

    return rows


def main():
    files = sorted(RAW_DIR.glob("*.csv"))

    if len(files) < 2:
        raise ValueError("At least two CSV datasets are required.")

    datasets = {}

    for file in files:
        if file.name in {
            "Dataset - Updated (1).csv"
        }:
            continue

        datasets[file.name] = load_dataset(file.name)

    print("\n" + "=" * 70)
    print("DATASET COMPARISON")
    print("=" * 70)

    all_columns = []
    all_values = []

    for filename, df in datasets.items():
        print(f"\n{'-' * 70}")
        print(f"DATASET: {filename}")
        print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")

        print("\nColumns:")
        for column in df.columns:
            print(f"  - {column}")

        print("\nDetailed information:")

        for column in df.columns:
            series = df[column]

            print(f"\n  {column}")
            print(f"    Type: {series.dtype}")
            print(f"    Missing: {series.isna().sum()}")
            print(f"    Unique: {series.nunique(dropna=True)}")

            if pd.api.types.is_numeric_dtype(series):
                print(f"    Range: {series.min()} → {series.max()}")
            else:
                values = series.dropna().unique()

                if len(values) <= 15:
                    print(f"    Values: {list(values)}")
                else:
                    print(f"    Sample values: {list(values[:10])}")

        all_columns.extend(column_summary(df, filename))
        all_values.extend(value_summary(df, filename))

    column_df = pd.DataFrame(all_columns)
    value_df = pd.DataFrame(all_values)

    column_df.to_csv(
        REPORT_DIR / "column_comparison.csv",
        index=False
    )

    value_df.to_csv(
        REPORT_DIR / "value_comparison.csv",
        index=False
    )

    # Compare column names
    column_sets = {
        filename: set(df.columns)
        for filename, df in datasets.items()
    }

    print("\n" + "=" * 70)
    print("COLUMN OVERLAP")
    print("=" * 70)

    for filename, columns in column_sets.items():
        print(f"\n{filename}:")
        print(f"  {len(columns)} columns")

    common_columns = set.intersection(*column_sets.values())

    print("\nCommon columns across all distinct datasets:")
    for column in sorted(common_columns):
        print(f"  - {column}")

    union_columns = set.union(*column_sets.values())

    print(f"\nTotal unique column names: {len(union_columns)}")

    print("\nAll unique columns:")
    for column in sorted(union_columns):
        print(f"  - {column}")

    # Target comparison
    print("\n" + "=" * 70)
    print("TARGET COMPARISON")
    print("=" * 70)

    target_candidates = [
        "risklevel",
        "risk_level",
        "risk",
        "risk_category",
        "riskcategory"
    ]

    for filename, df in datasets.items():

        target = next(
            (column for column in target_candidates if column in df.columns),
            None
        )

        print(f"\n{filename}")

        if target is None:
            print("  Target column not detected.")
            continue

        print(f"  Target column: {target}")
        print("  Distribution:")

        distribution = df[target].value_counts(dropna=False)

        for value, count in distribution.items():
            percentage = count / len(df) * 100
            print(
                f"    {value}: {count} "
                f"({percentage:.2f}%)"
            )

    print("\n" + "=" * 70)
    print("REPORTS CREATED")
    print("=" * 70)

    print(
        REPORT_DIR / "column_comparison.csv"
    )

    print(
        REPORT_DIR / "value_comparison.csv"
    )


if __name__ == "__main__":
    main()