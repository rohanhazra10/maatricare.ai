from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data" / "processed" / "baseline_dataset.csv"
MODEL_PATH = ROOT / "models" / "baseline_xgboost.pkl"
REPORTS = ROOT / "reports"

REPORTS.mkdir(exist_ok=True)

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


def build_model(seed):
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
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=seed,
            n_jobs=-1,
        )),
    ])


def main():

    df = pd.read_csv(INPUT)

    X = df[FEATURES]
    y = (df[TARGET] == "Low").astype(int)

    print("\nBASELINE ROBUSTNESS CHECK")
    print("=" * 50)

    # 1. Five-fold cross-validation
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    model = build_model(42)

    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=[
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
        ],
        n_jobs=-1,
    )

    cv_results = pd.DataFrame({
        "accuracy": scores["test_accuracy"],
        "precision": scores["test_precision"],
        "recall": scores["test_recall"],
        "f1": scores["test_f1"],
        "roc_auc": scores["test_roc_auc"],
    })

    cv_results.to_csv(
        REPORTS / "baseline_5fold_results.csv",
        index=False,
    )

    print("\n5-FOLD CROSS-VALIDATION")
    print(cv_results.round(4).to_string(index=False))

    print("\nMean ± Std:")
    for column in cv_results.columns:
        print(
            f"{column}: "
            f"{cv_results[column].mean():.4f} ± "
            f"{cv_results[column].std():.4f}"
        )

    # 2. Seed stability
    seeds = [7, 21, 42, 77, 123]
    seed_results = []

    for seed in seeds:

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            stratify=y,
            random_state=seed,
        )

        model = build_model(seed)
        model.fit(X_train, y_train)

        pred = model.predict_proba(X_test)[:, 1]

        seed_results.append({
            "seed": seed,
            "accuracy": (model.predict(X_test) == y_test).mean(),
            "roc_auc": roc_auc_score(y_test, pred),
        })

    seed_df = pd.DataFrame(seed_results)

    seed_df.to_csv(
        REPORTS / "baseline_seed_stability.csv",
        index=False,
    )

    print("\nSEED STABILITY")
    print(seed_df.round(4).to_string(index=False))

    print(
        f"\nAccuracy mean ± std: "
        f"{seed_df.accuracy.mean():.4f} ± "
        f"{seed_df.accuracy.std():.4f}"
    )

    print(
        f"ROC-AUC mean ± std: "
        f"{seed_df.roc_auc.mean():.4f} ± "
        f"{seed_df.roc_auc.std():.4f}"
    )

    # 3. Feature importance
    model = build_model(42)
    model.fit(X, y)

    xgb_model = model.named_steps["model"]

    importance = pd.DataFrame({
        "feature": FEATURES,
        "importance": xgb_model.feature_importances_,
    }).sort_values(
        "importance",
        ascending=False,
    )

    importance.to_csv(
        REPORTS / "baseline_feature_importance.csv",
        index=False,
    )

    print("\nFEATURE IMPORTANCE")
    print(importance.round(4).to_string(index=False))

    # 4. Permutation importance
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    model = build_model(42)
    model.fit(X_train, y_train)

    permutation = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="roc_auc",
        n_repeats=10,
        random_state=42,
        n_jobs=-1,
    )

    permutation_df = pd.DataFrame({
        "feature": FEATURES,
        "importance_mean": permutation.importances_mean,
        "importance_std": permutation.importances_std,
    }).sort_values(
        "importance_mean",
        ascending=False,
    )

    permutation_df.to_csv(
        REPORTS / "baseline_permutation_importance.csv",
        index=False,
    )

    print("\nPERMUTATION IMPORTANCE")
    print(permutation_df.round(4).to_string(index=False))

    # 5. Label-shuffle sanity check
    shuffled_scores = []

    for seed in seeds:

        rng = np.random.default_rng(seed)
        shuffled_y = rng.permutation(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            shuffled_y,
            test_size=0.20,
            stratify=shuffled_y,
            random_state=42,
        )

        model = build_model(seed)
        model.fit(X_train, y_train)

        probability = model.predict_proba(X_test)[:, 1]

        shuffled_scores.append({
            "seed": seed,
            "roc_auc": roc_auc_score(
                y_test,
                probability,
            ),
        })

    shuffled_df = pd.DataFrame(shuffled_scores)

    shuffled_df.to_csv(
        REPORTS / "baseline_label_shuffle.csv",
        index=False,
    )

    print("\nLABEL SHUFFLE SANITY CHECK")
    print(shuffled_df.round(4).to_string(index=False))

    print(
        f"\nShuffled ROC-AUC mean ± std: "
        f"{shuffled_df.roc_auc.mean():.4f} ± "
        f"{shuffled_df.roc_auc.std():.4f}"
    )

    print("\nReports saved:")
    print("reports/baseline_5fold_results.csv")
    print("reports/baseline_seed_stability.csv")
    print("reports/baseline_feature_importance.csv")
    print("reports/baseline_permutation_importance.csv")
    print("reports/baseline_label_shuffle.csv")


if __name__ == "__main__":
    main()