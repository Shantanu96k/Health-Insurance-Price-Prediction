# app/utils/suggestion_engine.py
"""
Suggestion Engine
==================
Rule-based health advice generator.

Returns precautions and improvement tips based on the predicted disease.

Why rule-based (not AI)?
  Simple, explainable, fast, and 100% deterministic.
  Perfect for a college project where you need to explain every output.

Easy to explain in viva:
  "Each disease maps to a list of medically reviewed precautions
   and improvements. We look up the disease and return the matching advice."
"""

# ── Advice database ───────────────────────────────────────────────────
_ADVICE = {

    "Heart Disease": {
        "precautions": [
            "Avoid smoking and all tobacco products immediately.",
            "Reduce salt, saturated fats, and fried food from your diet.",
            "Monitor your blood pressure daily if possible.",
            "Avoid heavy physical exertion without doctor clearance.",
            "Consult a cardiologist as soon as possible.",
        ],
        "improvements": [
            "Start a heart-healthy Mediterranean diet (fish, olive oil, vegetables).",
            "Walk 20–30 minutes daily at a comfortable pace.",
            "Practice stress reduction: meditation, yoga, or deep breathing.",
            "Sleep 7–8 hours per night — poor sleep raises cardiac risk.",
            "Get an ECG and lipid profile blood test done.",
        ],
    },

    "Diabetes Risk": {
        "precautions": [
            "Reduce sugar, white rice, white bread, and sugary drinks.",
            "Check your fasting blood sugar regularly.",
            "Maintain a healthy body weight — even 5% reduction helps.",
            "Avoid a sedentary lifestyle; take breaks from long sitting.",
            "Consult an endocrinologist for an HbA1c test.",
        ],
        "improvements": [
            "Add more fibre: whole grains, legumes, and green vegetables.",
            "Walk 20–30 minutes after every major meal.",
            "Replace sugar with natural alternatives like stevia.",
            "Stay well hydrated — drink 8–10 glasses of water daily.",
            "Get a full diabetes panel (FBS, PPBS, HbA1c) done.",
        ],
    },

    "Flu": {
        "precautions": [
            "Rest well and avoid going to work or crowded places.",
            "Stay hydrated — drink warm fluids, soups, and water.",
            "Wear a mask if you must step out to prevent spreading.",
            "Avoid cold food and drinks during recovery.",
        ],
        "improvements": [
            "Take Vitamin C (500mg), Vitamin D, and Zinc supplements.",
            "Get a flu vaccination every year before flu season.",
            "Maintain good hand hygiene — wash hands frequently.",
            "Steam inhalation can relieve congestion naturally.",
            "Consult a doctor if fever persists more than 3 days.",
        ],
    },

    "Allergy": {
        "precautions": [
            "Identify and avoid your specific allergy triggers.",
            "Keep antihistamine medication (cetirizine/loratadine) available.",
            "Avoid dusty, smoky, or heavily polluted environments.",
            "Do not rub your eyes if they feel itchy.",
        ],
        "improvements": [
            "Get an allergy panel test (skin prick or RAST test) done.",
            "Use an air purifier with HEPA filter in your room.",
            "Keep windows closed during high-pollen seasons.",
            "Shower and change clothes after spending time outdoors.",
            "Consult an allergist for long-term desensitisation therapy.",
        ],
    },

    "Hypertension": {
        "precautions": [
            "Reduce salt intake to less than 5g per day.",
            "Avoid caffeine, alcohol, and smoking.",
            "Monitor blood pressure at home twice daily.",
            "Avoid stressful situations and learn relaxation techniques.",
            "Consult a physician before stopping any BP medication.",
        ],
        "improvements": [
            "Follow the DASH diet (rich in potassium, calcium, magnesium).",
            "Exercise regularly — 150 minutes of moderate activity per week.",
            "Maintain a healthy weight; every kg lost reduces BP by 1 mmHg.",
            "Practice mindfulness or yoga for stress management.",
            "Get kidney function tests done — hypertension affects kidneys.",
        ],
    },

    "Cancer Risk": {
        "precautions": [
            "Stop smoking and avoid all tobacco products.",
            "Limit alcohol consumption strictly.",
            "Avoid prolonged sun exposure; use SPF 50+ sunscreen.",
            "Do not ignore unexplained weight loss, lumps, or bleeding.",
            "Consult an oncologist for cancer screening tests immediately.",
        ],
        "improvements": [
            "Eat a diet rich in antioxidants: berries, broccoli, green tea.",
            "Maintain a healthy BMI — obesity is a cancer risk factor.",
            "Get recommended cancer screenings (colonoscopy, mammogram, PSA).",
            "Exercise regularly — it reduces risk of several cancers.",
            "Manage stress — chronic stress suppresses the immune system.",
        ],
    },

    "No Significant Risk": {
        "precautions": [
            "Continue your current healthy habits.",
            "Do not ignore new or persistent symptoms — consult a doctor.",
            "Get a full body health checkup annually.",
        ],
        "improvements": [
            "Maintain a balanced diet rich in fruits and vegetables.",
            "Exercise for at least 150 minutes per week.",
            "Sleep 7–8 hours every night.",
            "Stay hydrated and limit junk food.",
            "Get routine blood tests (CBC, lipids, blood sugar) yearly.",
        ],
    },
}

# ── Default fallback ───────────────────────────────────────────────────
_DEFAULT = {
    "precautions": [
        "Consult a licensed doctor for a proper diagnosis.",
        "Do not self-medicate based on AI predictions.",
        "Keep a symptom diary to share with your doctor.",
    ],
    "improvements": [
        "Maintain a balanced diet and regular exercise routine.",
        "Drink at least 8 glasses of water daily.",
        "Get a full body health checkup annually.",
    ],
}


def get_suggestions(disease: str) -> dict:
    """
    Return precautions and improvements for a given disease.

    Args:
        disease: string name of the predicted disease

    Returns:
        {"precautions": [...], "improvements": [...]}
    """
    return _ADVICE.get(disease, _DEFAULT)
