# app/models/ml_model.py
"""
ML Prediction Model — Ensemble (Random Forest + Gradient Boosting + Naive Bayes)
==================================================================================
Post-Graduate Level ML:
  - Soft Voting Ensemble of 3 models for better accuracy
  - RandomForestClassifier (base)
  - GradientBoostingClassifier (boosting)
  - GaussianNaiveBayes (probabilistic baseline)
  - Confidence from averaged probability vectors
  - Risk determination using multi-factor weighted scoring

The model is loaded ONCE at import time for performance.
"""

import pickle
import os
import numpy as np

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

HIGH_RISK_DISEASES   = {"Heart Disease", "Diabetes Risk", "Cancer Risk"}
MEDIUM_RISK_DISEASES = {"Hypertension", "Allergy"}


# ── Load ensemble model ────────────────────────────────────────────────
ENSEMBLE = None
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "ml", "model.pkl"
)

def _load_model():
    global ENSEMBLE
    try:
        with open(MODEL_PATH, "rb") as f:
            ENSEMBLE = pickle.load(f)
        # Support both old single-model pkl and new ensemble dict
        if isinstance(ENSEMBLE, dict) and "models" in ENSEMBLE:
            print("[OK] Ensemble ML model loaded (RF + GB + NB).")
        else:
            print("[OK] ML model loaded (single RandomForest).")
    except FileNotFoundError:
        print("[WARN] ml/model.pkl not found. Run `python ml/train_model.py` first.")
        ENSEMBLE = None

_load_model()


# ── Prediction ─────────────────────────────────────────────────────────

def predict_disease(form_data: dict) -> dict:
    """
    Predicts disease using the loaded model (ensemble or single).
    Falls back to rule-based if model missing.
    """
    if ENSEMBLE is None:
        return _rule_based_fallback(form_data)

    features = _build_features(form_data)

    # Ensemble dict (new format from updated train_model.py)
    if isinstance(ENSEMBLE, dict) and "models" in ENSEMBLE:
        return _ensemble_predict(features, form_data)

    # Legacy single model
    return _single_predict(features, form_data)


def _build_features(form_data: dict) -> np.ndarray:
    features = []
    for col in FEATURE_COLUMNS:
        val = form_data.get(col, False)
        if isinstance(val, bool):
            features.append(int(val))
        elif isinstance(val, str):
            features.append(1 if val in ("1", "true", "True") else 0)
        else:
            features.append(int(val))
    return np.array(features).reshape(1, -1)


def _single_predict(features: np.ndarray, form_data: dict) -> dict:
    """Original single-model prediction."""
    model = ENSEMBLE  # legacy: ENSEMBLE holds the model directly
    predicted_disease = model.predict(features)[0]
    probabilities     = model.predict_proba(features)[0]
    confidence        = round(float(max(probabilities)) * 100, 1)
    risk_level        = _determine_risk(predicted_disease, confidence, form_data)
    return {
        "predicted_disease": predicted_disease,
        "confidence_score":  confidence,
        "risk_level":        risk_level,
        "model_used":        "RandomForest",
    }


def _ensemble_predict(features: np.ndarray, form_data: dict) -> dict:
    """Soft-voting ensemble prediction (RF + GB + NB)."""
    models  = ENSEMBLE["models"]
    classes = ENSEMBLE["classes"]

    # Average probability vectors across all models
    proba_sum = np.zeros(len(classes))
    for model in models:
        proba_sum += model.predict_proba(features)[0]
    avg_proba = proba_sum / len(models)

    best_idx          = int(np.argmax(avg_proba))
    predicted_disease = classes[best_idx]
    confidence        = round(float(avg_proba[best_idx]) * 100, 1)
    risk_level        = _determine_risk(predicted_disease, confidence, form_data)

    return {
        "predicted_disease": predicted_disease,
        "confidence_score":  confidence,
        "risk_level":        risk_level,
        "model_used":        "Ensemble(RF+GB+NB)",
        "class_probabilities": {
            cls: round(float(p) * 100, 1)
            for cls, p in zip(classes, avg_proba)
        },
    }


def _determine_risk(disease: str, confidence: float, form_data: dict) -> str:
    """
    Multi-factor weighted risk scoring.
    Score > 7 → high, 4–7 → medium, <4 → low
    """
    score = 0

    # Disease weight
    if disease in HIGH_RISK_DISEASES:
        score += 4
    elif disease in MEDIUM_RISK_DISEASES:
        score += 2

    # Confidence modifier
    if confidence >= 75:
        score += 2
    elif confidence >= 60:
        score += 1

    # Lifestyle risk factors (each adds weight)
    if form_data.get("smoker"):           score += 2
    if form_data.get("alcohol_use"):      score += 1
    if form_data.get("family_history_heart"):    score += 1
    if form_data.get("family_history_diabetes"): score += 1
    if form_data.get("family_history_cancer"):   score += 1
    if form_data.get("blood_pressure") == "high": score += 2
    if form_data.get("blood_sugar") == "high":    score += 2
    if form_data.get("exercise_frequency") == "never": score += 1
    if form_data.get("diet_quality") == "poor":   score += 1

    # Symptom severity
    serious_symptoms = ["chest_pain", "shortness_of_breath", "weight_loss"]
    for s in serious_symptoms:
        if form_data.get(s):
            score += 1

    if score >= 8:
        return "high"
    elif score >= 4:
        return "medium"
    return "low"


def _rule_based_fallback(form_data: dict) -> dict:
    """Simple rule-based fallback if model.pkl is missing."""
    has_chest    = form_data.get("chest_pain") or form_data.get("shortness_of_breath")
    has_heart_hx = form_data.get("family_history_heart") or form_data.get("smoker")
    has_sugar    = form_data.get("blood_sugar") == "high" or form_data.get("family_history_diabetes")
    has_fever    = form_data.get("fever") or form_data.get("cough")

    if has_chest and has_heart_hx:
        return {"predicted_disease": "Heart Disease",       "confidence_score": 72.0, "risk_level": "high",   "model_used": "RuleEngine"}
    if has_sugar:
        return {"predicted_disease": "Diabetes Risk",       "confidence_score": 65.0, "risk_level": "high",   "model_used": "RuleEngine"}
    if has_fever:
        return {"predicted_disease": "Flu",                 "confidence_score": 80.0, "risk_level": "low",    "model_used": "RuleEngine"}
    if form_data.get("skin_rash") or form_data.get("headache"):
        return {"predicted_disease": "Allergy",             "confidence_score": 58.0, "risk_level": "medium", "model_used": "RuleEngine"}
    return {"predicted_disease": "No Significant Risk",     "confidence_score": 55.0, "risk_level": "low",    "model_used": "RuleEngine"}


# ── Health Score (0–100 Wellness Index) ────────────────────────────────

def calculate_health_score(prediction_result: dict, form_data: dict) -> dict:
    """
    Calculate a composite Health Score from 0 (worst) to 100 (best).

    Scoring Formula (higher = healthier):
      - Disease component  (40 pts): based on predicted disease severity
      - Lifestyle component(35 pts): exercise, diet, smoker, alcohol, BP, sugar
      - Family history     (25 pts): genetic risk deductions

    Returns:
        {
            "score":    int (0–100),
            "grade":    str ("A" | "B" | "C" | "D" | "F"),
            "label":    str (human-readable label),
            "color":    str (CSS color for gauge),
            "breakdown": dict (sub-scores for each component)
        }

    Explain in viva:
      "We calculate a composite wellness score — inspired by credit scoring
       methodology applied to health. It gives a single number that summarises
       the patient's overall health status across disease risk, lifestyle
       quality, and genetic predisposition."
    """
    score = 100  # Start full, deduct for risks

    # ── Component 1: Disease severity (max deduction: 40 pts) ──────────
    disease = prediction_result.get("predicted_disease", "")
    confidence = prediction_result.get("confidence_score", 50)

    disease_deduction = 0
    if disease in HIGH_RISK_DISEASES:
        disease_deduction = int(30 + (confidence / 100) * 10)   # 30–40
    elif disease in MEDIUM_RISK_DISEASES:
        disease_deduction = int(15 + (confidence / 100) * 10)   # 15–25
    elif disease not in ("No Significant Risk", ""):
        disease_deduction = int(5 + (confidence / 100) * 5)     # 5–10

    score -= disease_deduction

    # ── Component 2: Lifestyle (max deduction: 35 pts) ─────────────────
    lifestyle_deduction = 0
    if form_data.get("smoker"):              lifestyle_deduction += 10
    if form_data.get("alcohol_use"):         lifestyle_deduction += 5
    if form_data.get("blood_pressure") == "high": lifestyle_deduction += 7
    if form_data.get("blood_sugar") == "high":    lifestyle_deduction += 7
    if form_data.get("exercise_frequency") == "never":    lifestyle_deduction += 4
    elif form_data.get("exercise_frequency") == "sometimes": lifestyle_deduction += 2
    if form_data.get("diet_quality") == "poor":    lifestyle_deduction += 4
    elif form_data.get("diet_quality") == "average": lifestyle_deduction += 1

    # Cap lifestyle at 35
    lifestyle_deduction = min(lifestyle_deduction, 35)
    score -= lifestyle_deduction

    # ── Component 3: Family history (max deduction: 25 pts) ────────────
    family_deduction = 0
    if form_data.get("family_history_heart"):    family_deduction += 8
    if form_data.get("family_history_diabetes"): family_deduction += 8
    if form_data.get("family_history_cancer"):   family_deduction += 9

    family_deduction = min(family_deduction, 25)
    score -= family_deduction

    # Clamp to 0–100
    score = max(0, min(100, score))

    # ── Grade mapping ──────────────────────────────────────────────────
    if score >= 85:
        grade, label, color = "A", "Excellent Health", "#10b981"
    elif score >= 70:
        grade, label, color = "B", "Good Health", "#22c55e"
    elif score >= 55:
        grade, label, color = "C", "Fair Health", "#f59e0b"
    elif score >= 35:
        grade, label, color = "D", "Poor Health", "#f97316"
    else:
        grade, label, color = "F", "Critical Risk", "#ef4444"

    return {
        "score": score,
        "grade": grade,
        "label": label,
        "color": color,
        "breakdown": {
            "disease":   100 - disease_deduction,
            "lifestyle": 100 - lifestyle_deduction,
            "family":    100 - family_deduction,
        }
    }