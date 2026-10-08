from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import optuna
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    brier_score_loss,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline

from xgboost import XGBClassifier


warnings.filterwarnings("ignore")

optuna.logging.set_verbosity(optuna.logging.WARNING)


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    ROOT
    / "data"
    / "processed"
    / "dataset_updated_clean.csv"
)

MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

MODEL_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

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

RANDOM_STATE = 42

TEST_SIZE = 0.20

CV_FOLDS = 5

OPTUNA_TRIALS = 50


# ============================================================
# MODEL BUILDER
# ============================================================

def build_model(params, seed=42):

    model = XGBClassifier(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        learning_rate=params["learning_rate"],
        min_child_weight=params["min_child_weight"],
        subsample=params["subsample"],
        colsample_bytree=params["colsample_bytree"],
        gamma=params["gamma"],
        reg_alpha=params["reg_alpha"],
        reg_lambda=params["reg_lambda"],
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=seed,
        n_jobs=-1,
    )

    return Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "model",
            model
        ),
    ])


# ============================================================
# DATA
# ============================================================

def load_data():

    df = pd.read_csv(DATA_FILE)

    df = df[FEATURES + [TARGET]].copy()

    df = df.dropna(subset=[TARGET])

    df[TARGET] = (
        df[TARGET]
        .astype(str)
        .str.strip()
        .str.title()
    )

    df = df[df[TARGET].isin(["Low", "High"])]

    df = df.drop_duplicates()

    X = df[FEATURES]

    # High = 1
    # Low = 0
    y = (
        df[TARGET]
        .map({
            "Low": 0,
            "High": 1
        })
        .astype(int)
    )

    return df, X, y


# ============================================================
# BASELINE MODEL
# ============================================================

def baseline_evaluation(X_train, y_train, X_test, y_test):

    params = {
        "n_estimators": 250,
        "max_depth": 4,
        "learning_rate": 0.05,
        "min_child_weight": 3,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "gamma": 0,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
    }

    model = build_model(params)

    model.fit(X_train, y_train)

    probability = model.predict_proba(X_test)[:, 1]

    prediction = (
        probability >= 0.5
    ).astype(int)

    return calculate_metrics(
        y_test,
        prediction,
        probability
    )


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(y_true, prediction, probability):

    return {
        "accuracy": accuracy_score(
            y_true,
            prediction
        ),
        "precision": precision_score(
            y_true,
            prediction,
            zero_division=0
        ),
        "recall_high": recall_score(
            y_true,
            prediction,
            zero_division=0
        ),
        "f1": f1_score(
            y_true,
            prediction,
            zero_division=0
        ),
        "roc_auc": roc_auc_score(
            y_true,
            probability
        ),
    }


# ============================================================
# OPTUNA
# ============================================================

def tune_model(X_train, y_train):

    cv = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    def objective(trial):

        params = {
            "n_estimators": trial.suggest_int(
                "n_estimators",
                150,
                800
            ),

            "max_depth": trial.suggest_int(
                "max_depth",
                2,
                8
            ),

            "learning_rate": trial.suggest_float(
                "learning_rate",
                0.01,
                0.20,
                log=True
            ),

            "min_child_weight": trial.suggest_int(
                "min_child_weight",
                1,
                10
            ),

            "subsample": trial.suggest_float(
                "subsample",
                0.60,
                1.0
            ),

            "colsample_bytree": trial.suggest_float(
                "colsample_bytree",
                0.60,
                1.0
            ),

            "gamma": trial.suggest_float(
                "gamma",
                0.0,
                5.0
            ),

            "reg_alpha": trial.suggest_float(
                "reg_alpha",
                0.0,
                2.0
            ),

            "reg_lambda": trial.suggest_float(
                "reg_lambda",
                0.5,
                5.0
            ),
        }

        model = build_model(params)

        scores = cross_validate(
            model,
            X_train,
            y_train,
            cv=cv,
            scoring={
                "recall": "recall",
                "precision": "precision",
                "f1": "f1",
                "roc_auc": "roc_auc",
            },
            n_jobs=-1,
        )

        recall = scores[
            "test_recall"
        ].mean()

        f1 = scores[
            "test_f1"
        ].mean()

        auc = scores[
            "test_roc_auc"
        ].mean()

        precision = scores[
            "test_precision"
        ].mean()

        # Balanced objective:
        # prioritize High-risk recall,
        # while preventing precision/F1/AUC
        # from being ignored.

        objective_score = (
            0.40 * recall
            + 0.25 * f1
            + 0.25 * auc
            + 0.10 * precision
        )

        return objective_score

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(
            seed=RANDOM_STATE
        ),
    )

    study.optimize(
        objective,
        n_trials=OPTUNA_TRIALS,
        show_progress_bar=True,
    )

    return study


# ============================================================
# CROSS VALIDATION OF FINAL MODEL
# ============================================================

def final_cross_validation(model, X_train, y_train):

    cv = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    scores = cross_validate(
        model,
        X_train,
        y_train,
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

    result = {}

    for metric in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ]:

        values = scores[
            f"test_{metric}"
        ]

        result[metric] = {
            "mean": float(values.mean()),
            "std": float(values.std()),
        }

    return result


# ============================================================
# THRESHOLD ANALYSIS
# ============================================================

def threshold_analysis(y_true, probability):

    rows = []

    for threshold in np.arange(
        0.30,
        0.71,
        0.05
    ):

        prediction = (
            probability >= threshold
        ).astype(int)

        rows.append({
            "threshold": round(
                float(threshold),
                2
            ),
            "accuracy": accuracy_score(
                y_true,
                prediction
            ),
            "precision_high": precision_score(
                y_true,
                prediction,
                zero_division=0
            ),
            "recall_high": recall_score(
                y_true,
                prediction,
                zero_division=0
            ),
            "f1": f1_score(
                y_true,
                prediction,
                zero_division=0
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nFINAL MATERNAL RISK BASELINE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df, X, y = load_data()

    print("\nDATASET")
    print("-" * 70)
    print(f"Rows: {len(df)}")
    print(f"Features: {len(FEATURES)}")
    print(f"Missing values: {X.isna().sum().sum()}")

    print("\nTarget:")
    print(
        df[TARGET]
        .value_counts()
    )

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    print("\nDATA SPLIT")
    print("-" * 70)
    print(f"Training: {len(X_train)}")
    print(f"Testing:  {len(X_test)}")

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    print("\nBASELINE MODEL")
    print("-" * 70)

    baseline = baseline_evaluation(
        X_train,
        y_train,
        X_test,
        y_test
    )

    for key, value in baseline.items():
        print(
            f"{key}: {value:.4f}"
        )

    # --------------------------------------------------------
    # Hyperparameter tuning
    # --------------------------------------------------------

    print("\nOPTUNA HYPERPARAMETER TUNING")
    print("-" * 70)
    print(
        f"Trials: {OPTUNA_TRIALS}"
    )
    print(
        f"CV folds: {CV_FOLDS}"
    )

    study = tune_model(
        X_train,
        y_train
    )

    best_params = study.best_params

    print("\nBEST PARAMETERS")
    print("-" * 70)

    for key, value in best_params.items():
        print(
            f"{key}: {value}"
        )

    print(
        f"\nBest tuning score: "
        f"{study.best_value:.4f}"
    )

    # --------------------------------------------------------
    # Final tuned model
    # --------------------------------------------------------

    final_model = build_model(
        best_params
    )

    print("\nFINAL CROSS-VALIDATION")
    print("-" * 70)

    cv_results = final_cross_validation(
        final_model,
        X_train,
        y_train
    )

    for metric, values in cv_results.items():

        print(
            f"{metric}: "
            f"{values['mean']:.4f} ± "
            f"{values['std']:.4f}"
        )

    # --------------------------------------------------------
    # Train final model
    # --------------------------------------------------------

    final_model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Test evaluation
    # --------------------------------------------------------

    probability = final_model.predict_proba(
        X_test
    )[:, 1]

    prediction = (
        probability >= 0.50
    ).astype(int)

    final_metrics = calculate_metrics(
        y_test,
        prediction,
        probability
    )

    print("\nFINAL TEST PERFORMANCE")
    print("-" * 70)

    for key, value in final_metrics.items():
        print(
            f"{key}: {value:.4f}"
        )

    print("\nConfusion Matrix:")
    print(
        confusion_matrix(
            y_test,
            prediction
        )
    )

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            prediction,
            target_names=[
                "Low",
                "High"
            ]
        )
    )

    # --------------------------------------------------------
    # Calibration
    # --------------------------------------------------------

    brier = brier_score_loss(
        y_test,
        probability
    )

    print("\nCALIBRATION")
    print("-" * 70)
    print(
        f"Brier score: {brier:.4f}"
    )

    fraction_positive, mean_predicted = (
        calibration_curve(
            y_test,
            probability,
            n_bins=10,
            strategy="quantile"
        )
    )

    calibration_df = pd.DataFrame({
        "mean_predicted_probability":
            mean_predicted,
        "fraction_positive":
            fraction_positive,
    })

    calibration_df.to_csv(
        REPORT_DIR
        / "final_calibration.csv",
        index=False
    )

    # --------------------------------------------------------
    # Threshold analysis
    # --------------------------------------------------------

    threshold_df = threshold_analysis(
        y_test,
        probability
    )

    threshold_df.to_csv(
        REPORT_DIR
        / "final_threshold_analysis.csv",
        index=False
    )

    print("\nTHRESHOLD ANALYSIS")
    print("-" * 70)
    print(
        threshold_df.round(4)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    xgb_model = (
        final_model
        .named_steps["model"]
    )

    importance_df = pd.DataFrame({
        "feature": FEATURES,
        "importance":
            xgb_model.feature_importances_,
    }).sort_values(
        "importance",
        ascending=False
    )

    importance_df.to_csv(
        REPORT_DIR
        / "final_feature_importance.csv",
        index=False
    )

    print("\nFEATURE IMPORTANCE")
    print("-" * 70)
    print(
        importance_df.round(4)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Permutation importance
    # --------------------------------------------------------

    permutation = permutation_importance(
        final_model,
        X_test,
        y_test,
        scoring="roc_auc",
        n_repeats=10,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    permutation_df = pd.DataFrame({
        "feature": FEATURES,
        "importance_mean":
            permutation.importances_mean,
        "importance_std":
            permutation.importances_std,
    }).sort_values(
        "importance_mean",
        ascending=False
    )

    permutation_df.to_csv(
        REPORT_DIR
        / "final_permutation_importance.csv",
        index=False
    )

    # --------------------------------------------------------
    # Save final metrics
    # --------------------------------------------------------

    report = {
        "dataset": "Dataset_Updated",
        "rows": int(len(df)),
        "features": FEATURES,
        "test_size": TEST_SIZE,
        "cv_folds": CV_FOLDS,
        "optuna_trials": OPTUNA_TRIALS,
        "baseline_metrics": baseline,
        "cross_validation": cv_results,
        "final_test_metrics": final_metrics,
        "brier_score": float(brier),
        "best_parameters": best_params,
    }

    with open(
        REPORT_DIR
        / "final_baseline_report.json",
        "w"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Save final model
    # --------------------------------------------------------

    artifact = {
        "model": final_model,
        "features": FEATURES,
        "target_mapping": {
            "Low": 0,
            "High": 1,
        },
        "threshold": 0.50,
        "dataset": "Dataset_Updated",
        "best_parameters": best_params,
    }

    joblib.dump(
        artifact,
        MODEL_DIR
        / "maatricare_baseline_xgboost.pkl"
    )

    print("\n" + "=" * 70)
    print("FINAL MODEL CREATED")
    print("=" * 70)

    print(
        "\nModel:"
        "\nmodels/maatricare_baseline_xgboost.pkl"
    )

    print(
        "\nReport:"
        "\nreports/final_baseline_report.json"
    )

    print("\nTraining pipeline completed.")


if __name__ == "__main__":
    main()