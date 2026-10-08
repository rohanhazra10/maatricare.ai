from pathlib import Path
import joblib
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]

TRAIN_FILE = ROOT / "data" / "processed" / "dataset_updated_clean.csv"
EXTERNAL_FILE = ROOT / "data" / "processed" / "maternal_risk_augmented_clean.csv"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"

REPORTS.mkdir(exist_ok=True)
MODELS.mkdir(exist_ok=True)

FEATURES = [
    "age",
    "systolic_bp",
    "diastolic",
    "bs",
    "body_temp",
    "heart_rate",
]


def build_model():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        ))
    ])


def main():

    print("\nCOMMON-FEATURE EXTERNAL VALIDATION")
    print("=" * 60)

    train_df = pd.read_csv(TRAIN_FILE)
    external_df = pd.read_csv(EXTERNAL_FILE)

    print(f"Training rows: {len(train_df)}")
    print(f"External rows: {len(external_df)}")

    train_df = train_df.dropna(subset=["risk_level"])

    X = train_df[FEATURES]
    y = train_df["risk_level"].map({
        "High": 0,
        "Low": 1
    })

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42
    )

    model = build_model()
    model.fit(X_train, y_train)

    print("\nINTERNAL HOLDOUT")
    print("-" * 60)

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    print(f"Accuracy:  {accuracy_score(y_test, pred):.4f}")
    print(f"Precision: {precision_score(y_test, pred):.4f}")
    print(f"Recall:    {recall_score(y_test, pred):.4f}")
    print(f"F1 Score:  {f1_score(y_test, pred):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_test, prob):.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, pred))

    # Rename external dataset column
    external_df = external_df.rename(
        columns={"diastolic_bp": "diastolic"}
    )

    X_external = external_df[FEATURES]

    external_pred = model.predict(X_external)
    external_prob = model.predict_proba(X_external)[:, 1]

    predicted_labels = pd.Series(external_pred).map({
        0: "High",
        1: "Low"
    })

    print("\nEXTERNAL PREDICTION DISTRIBUTION")
    print("-" * 60)
    print(predicted_labels.value_counts())

    # Low/High only
    mask = external_df["risk_level"].isin(["Low", "High"])

    y_external = external_df.loc[mask, "risk_level"].map({
        "High": 0,
        "Low": 1
    })

    pred_external = external_pred[mask]
    prob_external = external_prob[mask]

    print("\nEXTERNAL VALIDATION — LOW vs HIGH")
    print("-" * 60)

    accuracy = accuracy_score(y_external, pred_external)
    precision = precision_score(y_external, pred_external)
    recall = recall_score(y_external, pred_external)
    f1 = f1_score(y_external, pred_external)
    auc = roc_auc_score(y_external, prob_external)

    print(f"Samples:   {len(y_external)}")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_external, pred_external))

    print("\nClassification Report:")
    print(
        classification_report(
            y_external,
            pred_external,
            target_names=["High", "Low"]
        )
    )

    # Moderate analysis
    moderate = external_df["risk_level"] == "Moderate"

    print("\nMODERATE-RISK ANALYSIS")
    print("-" * 60)
    print(f"Moderate records: {moderate.sum()}")

    if moderate.sum() > 0:
        print(
            predicted_labels[moderate]
            .value_counts()
        )

        print(
            f"Mean Low probability: "
            f"{external_prob[moderate].mean():.4f}"
        )

    # Save predictions
    results = external_df.copy()

    results["predicted_risk"] = predicted_labels.values
    results["low_probability"] = external_prob
    results["high_probability"] = 1 - external_prob

    results.to_csv(
        REPORTS / "common_feature_external_predictions.csv",
        index=False
    )

    # Save metrics
    pd.DataFrame([{
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
        "samples": len(y_external),
        "moderate_samples": int(moderate.sum())
    }]).to_csv(
        REPORTS / "common_feature_external_metrics.csv",
        index=False
    )

    joblib.dump(
        {
            "pipeline": model,
            "features": FEATURES
        },
        MODELS / "common_feature_baseline.pkl"
    )

    print("\nVALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()