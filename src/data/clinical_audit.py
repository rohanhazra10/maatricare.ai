from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


DATASETS = {
    "Dataset - Updated.csv": {
        "age": (15, 55),
        "systolic_bp": (70, 200),
        "diastolic": (40, 140),
        "bs": (2, 25),
        "body_temp": (95, 105),
        "bmi": (10, 60),
        "heart_rate": (40, 180),
    },
    "Maternal_Health_Risk_Augmented.csv": {
        "age": (15, 55),
        "systolicbp": (70, 200),
        "diastolicbp": (40, 140),
        "bs": (2, 25),
        "bodytemp": (95, 105),
        "heartrate": (40, 180),
        "hemoglobin_g_dl": (5, 20),
        "bmi": (10, 60),
    },
}


def audit_dataset(filename, rules):
    path = RAW_DIR / filename

    if not path.exists():
        print(f"File not found: {filename}")
        return []

    df = pd.read_csv(path)

    findings = []

    for column, (minimum, maximum) in rules.items():

        if column not in df.columns:
            continue

        series = pd.to_numeric(df[column], errors="coerce")

        invalid = series.notna() & (
            (series < minimum) | (series > maximum)
        )

        invalid_rows = df.loc[invalid, [column]].copy()

        for index, row in invalid_rows.iterrows():
            findings.append({
                "dataset": filename,
                "row": int(index),
                "column": column,
                "value": row[column],
                "issue": "outside_plausibility_range",
                "allowed_min": minimum,
                "allowed_max": maximum
            })

    return findings


def check_special_cases(filename):
    path = RAW_DIR / filename

    if not path.exists():
        return []

    df = pd.read_csv(path)
    findings = []

    # BMI <= 0
    bmi_column = next(
        (c for c in ["bmi"] if c in df.columns),
        None
    )

    if bmi_column:
        values = pd.to_numeric(df[bmi_column], errors="coerce")
        invalid = values.notna() & (values <= 0)

        for index, value in values[invalid].items():
            findings.append({
                "dataset": filename,
                "row": int(index),
                "column": bmi_column,
                "value": value,
                "issue": "non_positive_bmi",
                "allowed_min": "> 0",
                "allowed_max": None
            })

    # Duplicate rows
    duplicate_count = int(df.duplicated().sum())

    if duplicate_count:
        findings.append({
            "dataset": filename,
            "row": None,
            "column": None,
            "value": duplicate_count,
            "issue": "duplicate_rows",
            "allowed_min": None,
            "allowed_max": None
        })

    # Missing values
    missing = df.isna().sum()

    for column, count in missing.items():
        if count > 0:
            findings.append({
                "dataset": filename,
                "row": None,
                "column": column,
                "value": int(count),
                "issue": "missing_values",
                "allowed_min": None,
                "allowed_max": None
            })

    return findings


def main():
    all_findings = []

    for filename, rules in DATASETS.items():
        print("\n" + "=" * 65)
        print(f"Auditing: {filename}")
        print("=" * 65)

        findings = audit_dataset(filename, rules)
        findings.extend(check_special_cases(filename))

        all_findings.extend(findings)

        if not findings:
            print("No suspicious values detected.")

        else:
            value_findings = [
                x for x in findings
                if x["issue"] not in {
                    "duplicate_rows",
                    "missing_values"
                }
            ]

            if value_findings:
                print("\nSuspicious values:")

                for item in value_findings:
                    print(
                        f"  Row {item['row']} | "
                        f"{item['column']} = {item['value']} | "
                        f"{item['issue']}"
                    )

            duplicate_findings = [
                x for x in findings
                if x["issue"] == "duplicate_rows"
            ]

            if duplicate_findings:
                print(
                    f"\nDuplicate rows: "
                    f"{duplicate_findings[0]['value']}"
                )

            missing_findings = [
                x for x in findings
                if x["issue"] == "missing_values"
            ]

            if missing_findings:
                print("\nMissing values:")

                for item in missing_findings:
                    print(
                        f"  {item['column']}: "
                        f"{item['value']}"
                    )

    report_path = REPORT_DIR / "clinical_audit.csv"

    if all_findings:
        pd.DataFrame(all_findings).to_csv(
            report_path,
            index=False
        )
    else:
        pd.DataFrame(
            columns=[
                "dataset",
                "row",
                "column",
                "value",
                "issue",
                "allowed_min",
                "allowed_max"
            ]
        ).to_csv(
            report_path,
            index=False
        )

    print("\n" + "=" * 65)
    print("CLINICAL AUDIT COMPLETE")
    print("=" * 65)
    print(f"\nReport saved to:")
    print(report_path)


if __name__ == "__main__":
    main()