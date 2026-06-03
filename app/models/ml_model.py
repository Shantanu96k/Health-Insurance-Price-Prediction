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


                                                                         
ENSEMBLE = None
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "ml", "model.pkl"
)

def _load_model():
    global ENSEMBLE
    try:
        with open(MODEL_PATH, "rb") as f:
            ENSEMBLE = pickle.load(f)
                                                                 
        if isinstance(ENSEMBLE, dict) and "models" in ENSEMBLE:
            print("[OK] Ensemble ML model loaded (RF + GB + NB).")
        else:
            print("[OK] ML model loaded (single RandomForest).")
    except FileNotFoundError:
        print("[WARN] ml/model.pkl not found. Run `python ml/train_model.py` first.")
        ENSEMBLE = None

_load_model()


                                                                         

def predict_disease(form_data: dict) -> dict:

       
    if ENSEMBLE is None:
        return _rule_based_fallback(form_data)

    features = _build_features(form_data)

                                                            
    if isinstance(ENSEMBLE, dict) and "models" in ENSEMBLE:
        return _ensemble_predict(features, form_data)

                         
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
                                           
    model = ENSEMBLE                                             
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
                                                         
    models  = ENSEMBLE["models"]
    classes = ENSEMBLE["classes"]

                                                   
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
       
    score = 0

                    
    if disease in HIGH_RISK_DISEASES:
        score += 4
    elif disease in MEDIUM_RISK_DISEASES:
        score += 2

                         
    if confidence >= 75:
        score += 2
    elif confidence >= 60:
        score += 1

                                               
    if form_data.get("smoker"):           score += 2
    if form_data.get("alcohol_use"):      score += 1
    if form_data.get("family_history_heart"):    score += 1
    if form_data.get("family_history_diabetes"): score += 1
    if form_data.get("family_history_cancer"):   score += 1
    if form_data.get("blood_pressure") == "high": score += 2
    if form_data.get("blood_sugar") == "high":    score += 2
    if form_data.get("exercise_frequency") == "never": score += 1
    if form_data.get("diet_quality") == "poor":   score += 1

                      
    serious_symptoms = ["chest_pain", "shortness_of_breath", "weight_loss"]
    for s in serious_symptoms:
        if form_data.get(s):
            score += 1

    if score >= 8:
        return       
    elif score >= 4:
        return         
    return      


def _rule_based_fallback(form_data: dict) -> dict:
                                                             
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


                                                                         

def calculate_health_score(prediction_result: dict, form_data: dict) -> dict:
           
    score = 100                                

                                                                         
    disease = prediction_result.get("predicted_disease", "")
    confidence = prediction_result.get("confidence_score", 50)

    disease_deduction = 0
    if disease in HIGH_RISK_DISEASES:
        disease_deduction = int(30 + (confidence / 100) * 10)          
    elif disease in MEDIUM_RISK_DISEASES:
        disease_deduction = int(15 + (confidence / 100) * 10)          
    elif disease not in ("No Significant Risk", ""):
        disease_deduction = int(5 + (confidence / 100) * 5)           

    score -= disease_deduction

                                                                         
    lifestyle_deduction = 0
    if form_data.get("smoker"):              lifestyle_deduction += 10
    if form_data.get("alcohol_use"):         lifestyle_deduction += 5
    if form_data.get("blood_pressure") == "high": lifestyle_deduction += 7
    if form_data.get("blood_sugar") == "high":    lifestyle_deduction += 7
    if form_data.get("exercise_frequency") == "never":    lifestyle_deduction += 4
    elif form_data.get("exercise_frequency") == "sometimes": lifestyle_deduction += 2
    if form_data.get("diet_quality") == "poor":    lifestyle_deduction += 4
    elif form_data.get("diet_quality") == "average": lifestyle_deduction += 1

                         
    lifestyle_deduction = min(lifestyle_deduction, 35)
    score -= lifestyle_deduction

                                                                         
    family_deduction = 0
    if form_data.get("family_history_heart"):    family_deduction += 8
    if form_data.get("family_history_diabetes"): family_deduction += 8
    if form_data.get("family_history_cancer"):   family_deduction += 9

    family_deduction = min(family_deduction, 25)
    score -= family_deduction

                    
    score = max(0, min(100, score))

                                                                         
    if score >= 85:
        grade, label, color = "A", "Excellent Health",          
    elif score >= 70:
        grade, label, color = "B", "Good Health",          
    elif score >= 55:
        grade, label, color = "C", "Fair Health",          
    elif score >= 35:
        grade, label, color = "D", "Poor Health",          
    else:
        grade, label, color = "F", "Critical Risk",          

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