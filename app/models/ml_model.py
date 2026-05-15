# app/models/ml_model.py
"""
ML Prediction Model
====================
Uses a pre-trained RandomForestClassifier (trained in ml/train_model.py).

The model is loaded ONCE when the app starts (module-level load),
so it's fast for every request — no re-loading on each call.

How RandomForest works (explain in viva):
  "We train 100 decision trees on patient symptom data.
   Each tree votes on a disease. The majority vote wins.
   We also get a confidence score from the vote percentages."
"""

import pickle
import os
import numpy as np

# ── Feature columns — MUST match the order used during training ────────
# These map directly to the form field names in patient.py
FEATURE_COLUMNS = [
    "fever",
    "cough",
    "chest_pain",
    "shortness_of_breath",
    "fatigue",
    "headache",
    "joint_pain",
    "skin_rash",
    "smoker",
    "family_history_diabetes",
    "family_history_heart",
]

# ── Diseases that are considered high risk ─────────────────────────────
HIGH_RISK_DISEASES  = {"Heart Disease", "Diabetes Risk", "Cancer Risk"}
MEDIUM_RISK_DISEASES = {"Hypertension", "Allergy"}


# ── Load model from disk (once at import time) ─────────────────────────
MODEL = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "model.pkl")

def _load_model():
    global MODEL
    try:
        with open(MODEL_PATH, "rb") as f:
            MODEL = pickle.load(f)
        print("✓ ML model loaded successfully.")
    except FileNotFoundError:
        print(
            "⚠  ml/model.pkl not found.\n"
            "   Run `python ml/train_model.py` first to train and save the model."
        )
        MODEL = None

_load_model()


# ── Prediction function ────────────────────────────────────────────────

def predict_disease(form_data: dict) -> dict:
    """
    Takes a dict of patient form answers and returns a prediction.

    Args:
        form_data: dict with keys matching FEATURE_COLUMNS (booleans or 0/1)

    Returns:
        {
            "predicted_disease": "Heart Disease",
            "confidence_score":  87.5,
            "risk_level":        "high"
        }

    Falls back to a rule-based prediction if the model is not loaded.
    """
    # ── If model is not available, use simple rule-based fallback ──────
    if MODEL is None:
        return _rule_based_fallback(form_data)

    # ── Build feature vector in correct order ──────────────────────────
    features = []
    for col in FEATURE_COLUMNS:
        val = form_data.get(col, False)
        # Convert True/False/1/0/"1"/"0" all to int
        if isinstance(val, bool):
            features.append(int(val))
        elif isinstance(val, str):
            features.append(1 if val in ("1", "true", "True") else 0)
        else:
            features.append(int(val))

    features_array = np.array(features).reshape(1, -1)

    # ── Predict ────────────────────────────────────────────────────────
    predicted_disease = MODEL.predict(features_array)[0]
    probabilities     = MODEL.predict_proba(features_array)[0]
    confidence        = round(float(max(probabilities)) * 100, 1)

    # ── Determine risk level ───────────────────────────────────────────
    risk_level = _determine_risk(predicted_disease, confidence, form_data)

    return {
        "predicted_disease": predicted_disease,
        "confidence_score":  confidence,
        "risk_level":        risk_level,
    }


def _determine_risk(disease: str, confidence: float, form_data: dict) -> str:
    """
    Map a predicted disease + confidence score → risk level.

    Logic:
      - High-risk disease + confidence ≥ 60%  → 'high'
      - High-risk disease + confidence < 60%  → 'medium'
      - Other disease + lifestyle risk factors → 'medium'
      - Otherwise                             → 'low'
    """
    # Check for additional lifestyle risk boosters
    lifestyle_risk = (
        form_data.get("smoker", False) or
        form_data.get("alcohol_use", False) or
        form_data.get("family_history_heart", False) or
        form_data.get("blood_pressure") == "high" or
        form_data.get("blood_sugar") == "high"
    )

    if disease in HIGH_RISK_DISEASES:
        return "high" if confidence >= 60 else "medium"

    if disease in MEDIUM_RISK_DISEASES or lifestyle_risk:
        return "medium"

    return "low"


def _rule_based_fallback(form_data: dict) -> dict:
    """
    Simple rule-based prediction used ONLY if model.pkl is missing.
    Not as accurate — just keeps the app working for demo purposes.
    Clearly not used in production.
    """
    has_chest    = form_data.get("chest_pain") or form_data.get("shortness_of_breath")
    has_heart_hx = form_data.get("family_history_heart") or form_data.get("smoker")
    has_sugar    = form_data.get("blood_sugar") == "high" or form_data.get("family_history_diabetes")
    has_fever    = form_data.get("fever") or form_data.get("cough")

    if has_chest and has_heart_hx:
        return {"predicted_disease": "Heart Disease",  "confidence_score": 72.0, "risk_level": "high"}
    if has_sugar:
        return {"predicted_disease": "Diabetes Risk",  "confidence_score": 65.0, "risk_level": "high"}
    if has_fever:
        return {"predicted_disease": "Flu",            "confidence_score": 80.0, "risk_level": "low"}
    if form_data.get("skin_rash") or form_data.get("headache"):
        return {"predicted_disease": "Allergy",        "confidence_score": 58.0, "risk_level": "medium"}

    return {"predicted_disease": "No Significant Risk", "confidence_score": 55.0, "risk_level": "low"}
