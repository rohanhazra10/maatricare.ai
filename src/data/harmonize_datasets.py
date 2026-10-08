from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


DATASETS = {
    "Dataset - Updated.csv": "dataset_updated_clean.csv",
    "Maternal_Health_Risk_Augmented.csv": "maternal_risk_augmented_clean.csv",
}


COLUMN_MAP = {
    "systolicbp": "systolic_bp",
    "diastolicbp": "diastolic_bp",
    "bodytemp": "body_temp",
    "heartrate": "heart_rate",
    "risklevel": "risk_level",
}


NUMERIC_COLUMNS = [
    "age",
    "systolic_bp",
    "diastolic_bp",
    "bs",
    "body_temp",
    "bmi",
    "heart_rate",
    "sleep_hours",
    "phys_activity_score",
    "stress_score",
    "diet_quality_score",
    "hemoglobin_g_dl",
]


def standardize_columns(df):
    df = df.copy()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    df = df.rename(columns=COLUMN_MAP)

    return df


def convert_numeric_columns(df):
    df = df.copy()

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def clean_risk_level(df):
    df = df.copy()

    if "risk_level" not in df.columns:
        return df

    df["risk_level"] = (
        df["risk_level"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    df["risk_level"] = df["risk_level"].replace({
        "low": "Low",
        "low risk": "Low",
        "mid": "Moderate",
        "mid risk": "Moderate",
        "medium": "Moderate",
        "moderate": "Moderate",
        "high": "High",
        "high risk": "High",
    })

    return df


def clean_invalid_values(df):
    df = df.copy()

    if "age" in df.columns:
        df.loc[
            ~df["age"].between(15, 55),
            "age"
        ] = pd.NA

    if "systolic_bp" in df.columns:
        df.loc[
            ~df["systolic_bp"].between(70, 200),
            "systolic_bp"
        ] = pd.NA

    if "diastolic_bp" in df.columns:
        df.loc[
            ~df["diastolic_bp"].between(40, 140),
            "diastolic_bp"
        ] = pd.NA

    if "diastolic" in df.columns:
        df.loc[
            ~df["diastolic"].between(40, 140),
            "diastolic"
        ] = pd.NA

    if "bs" in df.columns:
        df.loc[
            ~df["bs"].between(2, 25),
            "bs"
        ] = pd.NA

    if "body_temp" in df.columns:
        df.loc[
            ~df["body_temp"].between(95, 105),
            "body_temp"
        ] = pd.NA

    if "heart_rate" in df.columns:
        df.loc[
            ~df["heart_rate"].between(40, 180),
            "heart_rate"
        ] = pd.NA

    if "bmi" in df.columns:
        df.loc[
            df["bmi"] <= 0,
            "bmi"
        ] = pd.NA

    if "hemoglobin_g_dl" in df.columns:
        df.loc[
            ~df["hemoglobin_g_dl"].between(5, 20),
            "hemoglobin_g_dl"
        ] = pd.NA

    return df


def process_dataset(filename, output_filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    df = pd.read_csv(path)

    original_rows = len(df)

    df = standardize_columns(df)
    df = convert_numeric_columns(df)
    df = clean_risk_level(df)
    df = clean_invalid_values(df)

    duplicate_rows = int(df.duplicated().sum())

    df = df.drop_duplicates().reset_index(drop=True)

    df.insert(
        0,
        "data_source",
        filename
    )

    output_path = PROCESSED_DIR / output_filename
    df.to_csv(output_path, index=False)

    return {
        "dataset": filename,
        "original_rows": original_rows,
        "duplicate_rows_removed": duplicate_rows,
        "final_rows": len(df),
        "final_columns": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "output_file": output_filename,
    }


def main():
    reports = []

    for filename, output_filename in DATASETS.items():

        print("\n" + "=" * 65)
        print(f"Processing: {filename}")
        print("=" * 65)

        report = process_dataset(
            filename,
            output_filename
        )

        reports.append(report)

        print(
            f"Original rows: "
            f"{report['original_rows']}"
        )

        print(
            f"Duplicate rows removed: "
            f"{report['duplicate_rows_removed']}"
        )

        print(
            f"Final rows: "
            f"{report['final_rows']}"
        )

        print(
            f"Missing values: "
            f"{report['missing_values']}"
        )

        print(
            f"Saved: "
            f"{report['output_file']}"
        )

    pd.DataFrame(reports).to_csv(
        REPORT_DIR / "harmonization_summary.csv",
        index=False
    )

    print("\n" + "=" * 65)
    print("HARMONIZATION COMPLETE")
    print("=" * 65)

    print(
        f"\nSummary saved to:\n"
        f"{REPORT_DIR / 'harmonization_summary.csv'}"
    )


if __name__ == "__main__":
    main()