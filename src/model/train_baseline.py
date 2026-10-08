from pathlib import Path
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data" / "processed" / "baseline_dataset.csv"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

MODEL_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

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

    X = df[FEATURES]
    y = df[TARGET]

    encoder = LabelEncoder()
    y = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "model",
            XGBClassifier(
                n_estimators=250,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                reg_alpha=0.1,
                reg_lambda=1.0,
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=42,
                n_jobs=-1,
            )
        ),
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    cm = confusion_matrix(y_test, y_pred)

    print("\nBASELINE XGBOOST MODEL")
    print("=" * 40)

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")

    print("\nMetrics:")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")

    print("\nConfusion Matrix:")
    print(cm)

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=encoder.classes_,
        )
    )

    metrics = pd.DataFrame([{
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }])

    metrics.to_csv(
        REPORT_DIR / "baseline_metrics.csv",
        index=False,
    )

    artifact = {
        "pipeline": pipeline,
        "label_encoder": encoder,
        "features": FEATURES,
    }

    joblib.dump(
        artifact,
        MODEL_DIR / "baseline_xgboost.pkl",
    )

    print("\nSaved:")
    print("models/baseline_xgboost.pkl")
    print("reports/baseline_metrics.csv")


if __name__ == "__main__":
    main()