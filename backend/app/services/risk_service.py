from pathlib import Path

import joblib
import pandas as pd


# The model file lives in app/ml/
MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml"
    / "optimized_xgboost_pipeline.joblib"
)

# Order must match the order used during training
FEATURES = ["Age", "SBP", "DBP", "Temp_F", "HR", "BMI"]

CLASS_NAMES = {0: "High", 1: "Low", 2: "Mid"}

_model = None


class ModelRuntimeError(RuntimeError):
    """Raised when the serialized ML model cannot be used in this runtime."""


def get_model():
    """Load the model once, then reuse it."""
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception as exc:
            raise ModelRuntimeError(
                "The risk model could not be loaded. Install the pinned ML dependencies "
                "from requirements.txt (Python 3.12 is recommended) and verify the model file."
            ) from exc
    return _model


def predict_risk(age, sbp, dbp, temp_f, hr, bmi) -> dict:
    """Return risk category and class probabilities (in percent)."""
    model = get_model()

    data = pd.DataFrame(
        [[age, sbp, dbp, temp_f, hr, bmi]],
        columns=FEATURES,
    ).astype(float)

    try:
        predicted_class = int(model.predict(data)[0])
        probabilities = model.predict_proba(data)[0]
    except Exception as exc:
        raise ModelRuntimeError(
            "The risk model is incompatible with the installed ML runtime. "
            "Recreate the environment using requirements.txt and Python 3.12."
        ) from exc

    probability_results = {}
    for class_id, probability in zip(model.classes_, probabilities):
        probability_results[CLASS_NAMES[int(class_id)]] = round(
            float(probability) * 100, 2
        )

    return {
        "risk_category": CLASS_NAMES[predicted_class],
        "probabilities": probability_results,
        "model": "Optimized XGBoost",
        "clinical_status": (
            "Research prototype - not clinically validated. "
            "Not intended for diagnosis or treatment decisions."
        ),
    }
