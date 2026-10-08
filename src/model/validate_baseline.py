from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")


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

SUSPICIOUS = [
    "gestational_diabetes",
    "preexisting_diabetes",
    "bs",
    "mental_health",
    "previous_complications",
]


def build_model(seed=42):
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


def section(title):
    print("\n" + "=" * 65)
    print(title)
    print("=" * 65)


def basic_data_check(df):
    section("1. DATA QUALITY CHECK")

    print(f"Rows: {len(df)}")
    print(f"Features: {len(FEATURES)}")
    print(f"Duplicate rows: {df.duplicated().sum()}")
    print(f"Total missing values: {df[FEATURES].isna().sum().sum()}")

    print("\nMissing values:")
    print(df[FEATURES].isna().sum())

    print("\nTarget distribution:")
    print(df[TARGET].value_counts())

    print("\nTarget percentage:")
    print(
        (df[TARGET].value_counts(normalize=True) * 100)
        .round(2)
    )


def five_fold_cv(X, y):
    section("2. 5-FOLD CROSS-VALIDATION")

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    model = build_model()

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

    result = pd.DataFrame({
        "accuracy": scores["test_accuracy"],
        "precision": scores["test_precision"],
        "recall": scores["test_recall"],
        "f1": scores["test_f1"],
        "roc_auc": scores["test_roc_auc"],
    })

    result.to_csv(
        REPORTS / "validation_5fold.csv",
        index=False,
    )

    print(result.round(4).to_string(index=False))

    print("\nMean ± Std:")

    for col in result.columns:
        print(
            f"{col}: "
            f"{result[col].mean():.4f} ± "
            f"{result[col].std():.4f}"
        )

    return result


def seed_stability(X, y):
    section("3. RANDOM SEED STABILITY")

    seeds = [7, 21, 42, 77, 123]

    results = []

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

        pred = model.predict(X_test)
        prob = model.predict_proba(X_test)[:, 1]

        results.append({
            "seed": seed,
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred),
            "recall": recall_score(y_test, pred),
            "f1": f1_score(y_test, pred),
            "roc_auc": roc_auc_score(y_test, prob),
        })

    result = pd.DataFrame(results)

    result.to_csv(
        REPORTS / "validation_seed_stability.csv",
        index=False,
    )

    print(result.round(4).to_string(index=False))

    print("\nMean ± Std:")

    for col in result.columns[1:]:
        print(
            f"{col}: "
            f"{result[col].mean():.4f} ± "
            f"{result[col].std():.4f}"
        )

    return result


def holdout_evaluation(X, y):
    section("4. HOLDOUT TEST SET")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    model = build_model(42)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    results = {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, prob),
    }

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")

    for name, value in results.items():
        print(f"{name}: {value:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, pred))

    pd.DataFrame([results]).to_csv(
        REPORTS / "validation_holdout.csv",
        index=False,
    )


def single_feature_auc(X, y):
    section("5. SINGLE-FEATURE AUC TEST")

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    results = []

    for feature in FEATURES:

        model = build_model()

        scores = cross_validate(
            model,
            X[[feature]],
            y,
            cv=cv,
            scoring="roc_auc",
            n_jobs=-1,
        )

        results.append({
            "feature": feature,
            "auc_mean": scores["test_score"].mean(),
            "auc_std": scores["test_score"].std(),
        })

    result = pd.DataFrame(results).sort_values(
        "auc_mean",
        ascending=False,
    )

    result.to_csv(
        REPORTS / "validation_single_feature_auc.csv",
        index=False,
    )

    print(result.round(4).to_string(index=False))


def feature_ablation(X, y):
    section("6. FEATURE ABLATION")

    groups = {
        "all_features": FEATURES,

        "without_suspicious": [
            f for f in FEATURES
            if f not in SUSPICIOUS
        ],

        "clinical_vitals_only": [
            "age",
            "systolic_bp",
            "diastolic",
            "bs",
            "body_temp",
            "bmi",
            "heart_rate",
        ],

        "without_diabetes": [
            f for f in FEATURES
            if f not in [
                "gestational_diabetes",
                "preexisting_diabetes",
            ]
        ],

        "without_previous_complications": [
            f for f in FEATURES
            if f != "previous_complications"
        ],

        "without_mental_health": [
            f for f in FEATURES
            if f != "mental_health"
        ],
    }

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    results = []

    for name, feature_set in groups.items():

        model = build_model()

        scores = cross_validate(
            model,
            X[feature_set],
            y,
            cv=cv,
            scoring="roc_auc",
            n_jobs=-1,
        )

        results.append({
            "feature_set": name,
            "feature_count": len(feature_set),
            "auc_mean": scores["test_score"].mean(),
            "auc_std": scores["test_score"].std(),
        })

    result = pd.DataFrame(results)

    result.to_csv(
        REPORTS / "validation_feature_ablation.csv",
        index=False,
    )

    print(result.round(4).to_string(index=False))


def target_relationship(df):
    section("7. FEATURE / TARGET RELATIONSHIP")

    results = []

    for feature in FEATURES:

        temp = df[[feature, TARGET]].dropna()

        grouped = temp.groupby(TARGET)[feature].agg(
            ["mean", "median", "std", "min", "max"]
        )

        for risk, row in grouped.iterrows():

            results.append({
                "feature": feature,
                "risk_level": risk,
                "mean": row["mean"],
                "median": row["median"],
                "std": row["std"],
                "min": row["min"],
                "max": row["max"],
            })

    result = pd.DataFrame(results)

    result.to_csv(
        REPORTS / "validation_feature_target_relationship.csv",
        index=False,
    )

    print(result.round(3).to_string(index=False))


def categorical_relationship(df):
    section("8. CATEGORICAL FEATURE / TARGET RELATIONSHIP")

    results = []

    for feature in [
        "previous_complications",
        "preexisting_diabetes",
        "gestational_diabetes",
        "mental_health",
    ]:

        table = pd.crosstab(
            df[feature],
            df[TARGET],
            normalize="index",
        ) * 100

        print(f"\n{feature}")
        print(table.round(2))

        for value in table.index:

            row = {
                "feature": feature,
                "value": value,
            }

            for risk in table.columns:
                row[str(risk)] = table.loc[value, risk]

            results.append(row)

    pd.DataFrame(results).to_csv(
        REPORTS / "validation_categorical_relationship.csv",
        index=False,
    )


def permutation_importance_test(X, y):
    section("9. PERMUTATION IMPORTANCE")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    model = build_model()
    model.fit(X_train, y_train)

    result = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="roc_auc",
        n_repeats=10,
        random_state=42,
        n_jobs=-1,
    )

    importance = pd.DataFrame({
        "feature": FEATURES,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values(
        "importance_mean",
        ascending=False,
    )

    importance.to_csv(
        REPORTS / "validation_permutation_importance.csv",
        index=False,
    )

    print(importance.round(4).to_string(index=False))


def label_shuffle_test(X, y):
    section("10. LABEL SHUFFLE SANITY CHECK")

    seeds = [7, 21, 42, 77, 123]

    results = []

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

        prob = model.predict_proba(X_test)[:, 1]

        results.append({
            "seed": seed,
            "roc_auc": roc_auc_score(y_test, prob),
        })

    result = pd.DataFrame(results)

    result.to_csv(
        REPORTS / "validation_label_shuffle.csv",
        index=False,
    )

    print(result.round(4).to_string(index=False))

    print(
        f"\nMean shuffled AUC: "
        f"{result.roc_auc.mean():.4f} ± "
        f"{result.roc_auc.std():.4f}"
    )


def model_feature_importance(X, y):
    section("11. MODEL FEATURE IMPORTANCE")

    model = build_model()
    model.fit(X, y)

    xgb = model.named_steps["model"]

    result = pd.DataFrame({
        "feature": FEATURES,
        "importance": xgb.feature_importances_,
    }).sort_values(
        "importance",
        ascending=False,
    )

    result.to_csv(
        REPORTS / "validation_model_feature_importance.csv",
        index=False,
    )

    print(result.round(4).to_string(index=False))


def main():

    print("\nCOMPREHENSIVE BASELINE VALIDATION")
    print("=" * 65)

    df = pd.read_csv(INPUT)

    X = df[FEATURES]
    y = (df[TARGET] == "Low").astype(int)

    basic_data_check(df)
    five_fold_cv(X, y)
    seed_stability(X, y)
    holdout_evaluation(X, y)
    single_feature_auc(X, y)
    feature_ablation(X, y)
    target_relationship(df)
    categorical_relationship(df)
    permutation_importance_test(X, y)
    label_shuffle_test(X, y)
    model_feature_importance(X, y)

    print("\n" + "=" * 65)
    print("VALIDATION COMPLETE")
    print("=" * 65)

    print("\nAll validation reports saved in:")
    print(REPORTS)


if __name__ == "__main__":
    main()