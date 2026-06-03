                             
   

from typing import Optional

                                                                       
                                                      
                                                                        
                                                                       

DO_TIPS = [
    {
        "text": "Consult a cardiologist within the next 14 days for an ECG and lipid profile.",
        "conditions": ["disease:Heart Disease", "disease:Hypertension"],
        "priority": 5,
    },
    {
        "text": "Monitor your blood pressure twice daily (morning and evening) and keep a log.",
        "conditions": ["disease:Hypertension", "disease:Heart Disease", "bp:high"],
        "priority": 5,
    },
    {
        "text": "Schedule a fasting blood sugar (FBS) and HbA1c test immediately.",
        "conditions": ["disease:Diabetes Risk", "sugar:high", "family:diabetes"],
        "priority": 5,
    },
    {
        "text": "Get a complete blood count (CBC), LFT, and kidney function test done.",
        "conditions": ["risk:high"],
        "priority": 4,
    },
    {
        "text": "Drink at least 8–10 glasses of water daily to flush toxins and stay hydrated.",
        "conditions": ["always"],
        "priority": 2,
    },
    {
        "text": "Take a 10-minute walk after every meal — even a short walk improves insulin sensitivity.",
        "conditions": ["disease:Diabetes Risk", "sugar:high", "exercise:never"],
        "priority": 4,
    },
    {
        "text": "Sleep 7–8 hours every night — poor sleep raises cortisol and worsens all chronic conditions.",
        "conditions": ["risk:high", "risk:medium"],
        "priority": 3,
    },
    {
        "text": "Practice deep breathing for 5 minutes every morning to lower your resting heart rate.",
        "conditions": ["disease:Hypertension", "disease:Heart Disease", "symptom:chest_pain"],
        "priority": 4,
    },
    {
        "text": "Carry your allergy medication (antihistamine) at all times during season changes.",
        "conditions": ["disease:Allergy"],
        "priority": 4,
    },
    {
        "text": "Get a flu vaccination every year before October.",
        "conditions": ["disease:Flu"],
        "priority": 3,
    },
    {
        "text": "Visit a licensed doctor for a comprehensive health checkup every 6 months.",
        "conditions": ["risk:high", "risk:medium"],
        "priority": 4,
    },
    {
        "text": "Keep a daily symptom diary — note when symptoms worsen, what you ate, and activity level.",
        "conditions": ["risk:medium", "risk:high"],
        "priority": 3,
    },
    {
        "text": "Wear sunscreen SPF 50+ daily if you have a family history of cancer.",
        "conditions": ["family:cancer", "disease:Cancer Risk"],
        "priority": 4,
    },
    {
        "text": "Get cancer screening tests: colonoscopy (age 45+), PSA test for men, mammogram for women.",
        "conditions": ["disease:Cancer Risk", "family:cancer"],
        "priority": 5,
    },
    {
        "text": "Use an air purifier (HEPA filter) at home — especially in Nagpur's high-pollution months.",
        "conditions": ["disease:Allergy", "symptom:cough", "symptom:shortness_of_breath"],
        "priority": 3,
    },
]

DONT_TIPS = [
    {
        "text": "Do NOT smoke or use any tobacco product — it is the single biggest risk factor for heart disease and cancer.",
        "conditions": ["smoker:yes"],
        "priority": 5,
    },
    {
        "text": "Do NOT consume alcohol — it raises blood pressure, damages the liver, and worsens diabetes.",
        "conditions": ["alcohol:yes", "disease:Diabetes Risk", "disease:Hypertension"],
        "priority": 5,
    },
    {
        "text": "Do NOT eat white rice, white bread, or sugary drinks — these spike blood sugar rapidly.",
        "conditions": ["disease:Diabetes Risk", "sugar:high"],
        "priority": 5,
    },
    {
        "text": "Do NOT ignore chest pain or breathlessness — these are emergency warning signs.",
        "conditions": ["symptom:chest_pain", "symptom:shortness_of_breath"],
        "priority": 5,
    },
    {
        "text": "Do NOT add extra salt to food — excess sodium directly raises blood pressure.",
        "conditions": ["disease:Hypertension", "bp:high", "disease:Heart Disease"],
        "priority": 4,
    },
    {
        "text": "Do NOT self-medicate — always consult a doctor before starting or stopping any medication.",
        "conditions": ["risk:high"],
        "priority": 4,
    },
    {
        "text": "Do NOT skip meals — irregular eating patterns worsen blood sugar control.",
        "conditions": ["disease:Diabetes Risk", "sugar:high"],
        "priority": 4,
    },
    {
        "text": "Do NOT consume processed meats, fried food, or packaged junk food.",
        "conditions": ["disease:Heart Disease", "disease:Cancer Risk", "risk:high"],
        "priority": 4,
    },
    {
        "text": "Do NOT sit for more than 45 minutes without taking a 5-minute walk break.",
        "conditions": ["exercise:never", "disease:Diabetes Risk", "disease:Hypertension"],
        "priority": 3,
    },
    {
        "text": "Do NOT rub your eyes or touch your face during allergy season.",
        "conditions": ["disease:Allergy", "symptom:skin_rash"],
        "priority": 3,
    },
    {
        "text": "Do NOT delay medical consultation if symptoms persist more than 3 days.",
        "conditions": ["symptom:fever", "symptom:cough", "disease:Flu"],
        "priority": 4,
    },
    {
        "text": "Do NOT consume alcohol while taking antihistamines or BP medication.",
        "conditions": ["alcohol:yes", "disease:Allergy", "disease:Hypertension"],
        "priority": 5,
    },
]

IMPROVE_TIPS = [
    {
        "text": "Start a Mediterranean diet: olive oil, fish, leafy greens, legumes, and whole grains.",
        "conditions": ["disease:Heart Disease", "disease:Hypertension"],
        "priority": 5,
    },
    {
        "text": "Gradually increase physical activity — start with 20 min walks and build to 150 min/week.",
        "conditions": ["exercise:never", "risk:medium", "risk:high"],
        "priority": 4,
    },
    {
        "text": "Practice stress management: 15 minutes of meditation or yoga daily reduces cortisol by 20%.",
        "conditions": ["disease:Hypertension", "disease:Heart Disease", "risk:high"],
        "priority": 4,
    },
    {
        "text": "Quit smoking — even reducing by 50% measurably improves lung function within weeks.",
        "conditions": ["smoker:yes"],
        "priority": 5,
    },
    {
        "text": "Reduce alcohol to maximum 1 unit per week or eliminate entirely.",
        "conditions": ["alcohol:yes"],
        "priority": 4,
    },
    {
        "text": "Improve sleep hygiene: fixed sleep/wake time, no screens 1hr before bed, dark cool room.",
        "conditions": ["risk:high", "risk:medium", "symptom:fatigue"],
        "priority": 3,
    },
    {
        "text": "Track your food intake for 30 days using an app — awareness is the first step to change.",
        "conditions": ["diet:poor", "disease:Diabetes Risk", "disease:Hypertension"],
        "priority": 3,
    },
    {
        "text": "Join a community health program or gym — social accountability doubles habit success.",
        "conditions": ["exercise:never", "exercise:sometimes"],
        "priority": 2,
    },
    {
        "text": "Get an allergy panel test done — identifying specific triggers enables targeted treatment.",
        "conditions": ["disease:Allergy"],
        "priority": 4,
    },
    {
        "text": "Set up a home blood pressure monitor (₹800–1,200) and log readings daily.",
        "conditions": ["disease:Hypertension", "bp:high"],
        "priority": 4,
    },
    {
        "text": "Consider cognitive-behavioural therapy (CBT) for stress and anxiety management.",
        "conditions": ["symptom:headache", "risk:high"],
        "priority": 3,
    },
    {
        "text": "Reduce BMI by 5–7% through calorie-aware eating — this alone can reverse pre-diabetes.",
        "conditions": ["disease:Diabetes Risk"],
        "priority": 4,
    },
]

DIET_TIPS = [
    {
        "text": "Eat 5 portions of vegetables and 2 of fruit every day — focus on colour variety.",
        "conditions": ["always"],
        "priority": 3,
    },
    {
        "text": "Replace white rice with brown rice or millets (jowar, bajra, ragi) — they have lower glycaemic index.",
        "conditions": ["disease:Diabetes Risk", "sugar:high"],
        "priority": 5,
    },
    {
        "text": "Include 30g of nuts (almonds, walnuts) daily — they protect the heart and reduce LDL cholesterol.",
        "conditions": ["disease:Heart Disease", "disease:Hypertension"],
        "priority": 4,
    },
    {
        "text": "Add turmeric and ginger to your daily cooking — both have anti-inflammatory properties.",
        "conditions": ["symptom:joint_pain", "disease:Allergy"],
        "priority": 3,
    },
    {
        "text": "Eat high-fibre foods: whole dals, rajma, chana, and vegetables — fibre stabilises blood sugar.",
        "conditions": ["disease:Diabetes Risk", "disease:Heart Disease"],
        "priority": 4,
    },
    {
        "text": "Consume 2–3 servings of low-fat dairy (dahi, buttermilk) daily for calcium and probiotics.",
        "conditions": ["disease:Hypertension"],
        "priority": 3,
    },
    {
        "text": "Eat omega-3 rich foods: flaxseeds, chia seeds, fish (if non-veg) — reduces cardiac inflammation.",
        "conditions": ["disease:Heart Disease", "disease:Cancer Risk"],
        "priority": 4,
    },
    {
        "text": "Switch to rock salt or low-sodium salt and use herbs for flavouring instead.",
        "conditions": ["disease:Hypertension", "bp:high"],
        "priority": 4,
    },
    {
        "text": "Add methi (fenugreek) seeds soaked overnight to your morning routine — controls blood sugar.",
        "conditions": ["disease:Diabetes Risk"],
        "priority": 3,
    },
    {
        "text": "Avoid fruit juices — eat whole fruit instead to preserve fibre and avoid sugar spikes.",
        "conditions": ["disease:Diabetes Risk", "sugar:high"],
        "priority": 4,
    },
    {
        "text": "Drink green tea (1–2 cups/day) — it contains catechins that reduce cancer and heart risk.",
        "conditions": ["disease:Cancer Risk", "disease:Heart Disease"],
        "priority": 3,
    },
    {
        "text": "Eat your heaviest meal at lunch, light dinner — better digestion and metabolic alignment.",
        "conditions": ["always"],
        "priority": 2,
    },
]

EXERCISE_TIPS = [
    {
        "text": "Start with 20-minute brisk walks 5 days/week — this is proven to reduce cardiac risk by 30%.",
        "conditions": ["exercise:never", "disease:Heart Disease", "disease:Hypertension"],
        "priority": 5,
    },
    {
        "text": "Do 150 minutes of moderate aerobic exercise per week (WHO recommendation for chronic disease).",
        "conditions": ["risk:high", "risk:medium"],
        "priority": 4,
    },
    {
        "text": "Add resistance training 2 days/week — muscle mass improves insulin sensitivity by 20–30%.",
        "conditions": ["disease:Diabetes Risk", "exercise:sometimes"],
        "priority": 4,
    },
    {
        "text": "Practice yoga 30 minutes daily — combines physical conditioning with proven stress reduction.",
        "conditions": ["disease:Hypertension", "symptom:headache", "risk:medium"],
        "priority": 4,
    },
    {
        "text": "Swimming is ideal for joint pain — zero impact on joints while improving cardiovascular fitness.",
        "conditions": ["symptom:joint_pain"],
        "priority": 4,
    },
    {
        "text": "Use stairs instead of lifts and walk for trips under 1 km — lifestyle activity counts.",
        "conditions": ["exercise:never"],
        "priority": 3,
    },
    {
        "text": "Do gentle stretching for 10 minutes every morning to reduce joint stiffness.",
        "conditions": ["symptom:joint_pain"],
        "priority": 3,
    },
    {
        "text": "Maintain exercise even during Flu recovery — light walking (not strenuous) speeds up recovery.",
        "conditions": ["disease:Flu"],
        "priority": 3,
    },
    {
        "text": "Cycle 30–45 minutes 3x/week — excellent for diabetes management and cardiovascular health.",
        "conditions": ["disease:Diabetes Risk", "exercise:sometimes"],
        "priority": 3,
    },
    {
        "text": "Include balance exercises (standing on one leg, tai chi) — reduces fall risk as you age.",
        "conditions": ["always"],
        "priority": 2,
    },
]


def _build_conditions(prediction_result: dict, form_data: dict) -> set:
       
    tags = {"always"}

             
    disease = prediction_result.get("predicted_disease", "")
    if disease:
        tags.add(f"disease:{disease}")

                
    risk = prediction_result.get("risk_level", "low")
    tags.add(f"risk:{risk}")

               
    if form_data.get("smoker"):
        tags.add("smoker:yes")
    if form_data.get("alcohol_use"):
        tags.add("alcohol:yes")

    exercise = form_data.get("exercise_frequency", "sometimes")
    tags.add(f"exercise:{exercise}")

    diet = form_data.get("diet_quality", "average")
    tags.add(f"diet:{diet}")

    if form_data.get("blood_pressure") == "high":
        tags.add("bp:high")
    if form_data.get("blood_sugar") == "high":
        tags.add("sugar:high")

                    
    if form_data.get("family_history_heart"):
        tags.add("family:heart")
    if form_data.get("family_history_diabetes"):
        tags.add("family:diabetes")
    if form_data.get("family_history_cancer"):
        tags.add("family:cancer")

              
    symptoms = [
        "fever", "cough", "chest_pain", "shortness_of_breath",
        "fatigue", "headache", "joint_pain", "skin_rash", "nausea", "weight_loss"
    ]
    for s in symptoms:
        if form_data.get(s):
            tags.add(f"symptom:{s}")

    return tags


def _select_tips(tip_library: list, patient_tags: set, max_tips: int = 5) -> list:
       
    scored = []
    for tip in tip_library:
        matched = False
        score   = 0
        for cond in tip["conditions"]:
            if cond in patient_tags:
                matched = True
                score  += tip["priority"]
        if matched:
            scored.append((score, tip["text"]))

                                          
    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:max_tips]]


def get_ai_health_tips(prediction_result: dict, form_data: dict) -> dict:
       
    tags = _build_conditions(prediction_result, form_data)

    do_list       = _select_tips(DO_TIPS,      tags, max_tips=5)
    dont_list     = _select_tips(DONT_TIPS,    tags, max_tips=5)
    improve_list  = _select_tips(IMPROVE_TIPS, tags, max_tips=4)
    diet_list     = _select_tips(DIET_TIPS,    tags, max_tips=4)
    exercise_list = _select_tips(EXERCISE_TIPS, tags, max_tips=3)

                     
    disease = prediction_result.get("predicted_disease", "your condition")
    risk    = prediction_result.get("risk_level", "medium")
    confidence = prediction_result.get("confidence_score", 0)

    if risk == "high":
        summary = (
            f"Your assessment shows a HIGH risk profile with {disease} predicted "
            f"at {confidence}% confidence. Immediate medical consultation is strongly recommended. "
            "Follow the tips below to reduce your risk and improve your quality of life."
        )
    elif risk == "medium":
        summary = (
            f"Your assessment shows a MODERATE risk profile with {disease} predicted "
            f"at {confidence}% confidence. Proactive lifestyle changes now can prevent escalation. "
            "Follow the personalised tips below for your health journey."
        )
    else:
        summary = (
            f"Your assessment shows a LOW risk profile with {disease} predicted "
            f"at {confidence}% confidence. Continue your healthy habits and maintain "
            "regular annual checkups. Small improvements can further strengthen your health."
        )

    return {
        "do":       do_list,
        "dont":     dont_list,
        "improve":  improve_list,
        "diet":     diet_list,
        "exercise": exercise_list,
        "summary":  summary,
    }