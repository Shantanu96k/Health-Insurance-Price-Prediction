import pickle
import os
import numpy as np

_MODEL_DATA = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'insurance_model.pkl')


def _load():
    global _MODEL_DATA
    try:
        with open(MODEL_PATH, 'rb') as f:
            _MODEL_DATA = pickle.load(f)
        print('[OK] Insurance price model loaded.')
    except FileNotFoundError:
        print('[WARN]  ml/insurance_model.pkl not found. Run python ml/train_insurance_model.py')
        _MODEL_DATA = None


_load()


REGION_MAP = {'north': 0, 'south': 1, 'east': 2, 'west': 3}
EXERCISE_MAP = {'never': 0, 'sometimes': 1, 'regular': 2}
DIET_MAP = {'poor': 0, 'average': 1, 'good': 2}


def predict_insurance_price(form_data: dict) -> dict:
    if _MODEL_DATA is None:
        return _fallback(form_data)

    model = _MODEL_DATA['model']
    cols = _MODEL_DATA['feature_columns']

    age = int(form_data.get('age', 30))
    bmi = float(form_data.get('bmi', 25.0))
    children = int(form_data.get('children', 0))
    smoker = 1 if form_data.get('smoker') else 0
    region = REGION_MAP.get(str(form_data.get('region', 'north')), 0)
    sex = 0 if str(form_data.get('sex', 'male')).lower() == 'male' else 1
    has_diab = 1 if form_data.get('has_diabetes') else 0
    has_heart = 1 if form_data.get('has_heart') else 0
    has_bp = 1 if form_data.get('has_bp') else 0
    exercise = EXERCISE_MAP.get(str(form_data.get('exercise_frequency', 'sometimes')), 1)
    diet = DIET_MAP.get(str(form_data.get('diet_quality', 'average')), 1)

    features = np.array([[age, bmi, children, smoker, region, sex,
                          has_diab, has_heart, has_bp, exercise, diet]])

    annual = int(round(model.predict(features)[0], -2))
    monthly = int(annual / 12)

    if annual < 8000:
        band = 'budget'
    elif annual < 20000:
        band = 'standard'
    else:
        band = 'premium'

    risk_factors = []
    if smoker:
        risk_factors.append('Smoker — significantly increases premium')
    if has_diab:
        risk_factors.append('Diabetes — requires higher coverage')
    if has_heart:
        risk_factors.append('Heart condition — critical illness risk')
    if has_bp:
        risk_factors.append('High BP — cardiovascular risk factor')
    if bmi > 30:
        risk_factors.append(f'High BMI ({bmi}) — obesity risk factor')
    if age > 45:
        risk_factors.append(f'Age {age} — higher age group')
    if exercise == 0:
        risk_factors.append('Sedentary lifestyle — no exercise')
    if children > 2:
        risk_factors.append(f'{children} dependents — family coverage')

    breakdown = {
        'base': 4000,
        'age': age * 220,
        'bmi': int(bmi * 180),
        'smoker': smoker * 18000,
        'conditions': (has_diab * 9000) + (has_heart * 12000) + (has_bp * 5000),
        'lifestyle': ((2 - exercise) * 1500) + ((2 - diet) * 800),
        'dependents': children * 1200,
    }

    return {
        'annual_premium': annual,
        'monthly_premium': monthly,
        'premium_band': band,
        'breakdown': breakdown,
        'risk_factors': risk_factors,
    }


def _fallback(form_data: dict) -> dict:
    age = int(form_data.get('age', 30))
    smoker = 1 if form_data.get('smoker') else 0
    annual = 6000 + age * 200 + smoker * 15000
    return {
        'annual_premium': annual,
        'monthly_premium': annual // 12,
        'premium_band': 'standard',
        'breakdown': {},
        'risk_factors': ['Model not loaded — approximate estimate'],
    }
