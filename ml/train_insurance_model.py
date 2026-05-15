# ml/train_insurance_model.py
"""
Insurance Price Prediction Model
==================================
Run ONCE before starting server:
    python ml/train_insurance_model.py

What it does:
  1. Builds a synthetic insurance dataset (age, bmi, smoker, region, children, conditions)
  2. Trains a GradientBoostingRegressor
  3. Saves model + feature metadata to ml/insurance_model.pkl

Why GradientBoosting?
  - Handles mixed features (numeric + categorical) well
  - Gives feature importances (good for viva)
  - Better accuracy than linear regression on this type of data

In real world: Use publicly available insurance datasets (Kaggle Medical Cost Dataset)
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

FEATURE_COLUMNS = [
    "age",
    "bmi",
    "children",
    "smoker",          # 0 or 1
    "region_encoded",  # 0-3
    "sex_encoded",     # 0 or 1
    "has_diabetes",    # 0 or 1
    "has_heart",       # 0 or 1
    "has_bp",          # 0 or 1
    "exercise_score",  # 0=never, 1=sometimes, 2=regular
    "diet_score",      # 0=poor, 1=average, 2=good
]

# ── Synthetic training data ─────────────────────────────────────────
# In a real project, use the Kaggle Medical Cost Dataset:
# https://www.kaggle.com/datasets/mirichoi0218/insurance
# Base prices in INR (roughly 30x USD equivalent)
np.random.seed(42)
N = 800

ages       = np.random.randint(18, 65, N)
bmis       = np.round(np.random.normal(28, 6, N).clip(15, 50), 1)
children   = np.random.randint(0, 5, N)
smoker     = np.random.binomial(1, 0.2, N)
region     = np.random.randint(0, 4, N)    # north/south/east/west
sex        = np.random.randint(0, 2, N)    # 0=male, 1=female
has_diab   = np.random.binomial(1, 0.1, N)
has_heart  = np.random.binomial(1, 0.07, N)
has_bp     = np.random.binomial(1, 0.15, N)
exercise   = np.random.randint(0, 3, N)
diet       = np.random.randint(0, 3, N)

# Price formula (realistic INR annual premium)
base = 4000
prices = (
    base
    + ages * 220
    + bmis * 180
    + children * 1200
    + smoker * 18000
    + has_diab * 9000
    + has_heart * 12000
    + has_bp * 5000
    + (2 - exercise) * 1500
    + (2 - diet) * 800
    + np.random.normal(0, 2000, N)  # noise
).clip(3000, None)

df = pd.DataFrame({
    "age": ages, "bmi": bmis, "children": children,
    "smoker": smoker, "region_encoded": region, "sex_encoded": sex,
    "has_diabetes": has_diab, "has_heart": has_heart, "has_bp": has_bp,
    "exercise_score": exercise, "diet_score": diet,
    "annual_premium": prices.round(0).astype(int)
})

print(f"\n📊 Dataset: {len(df)} rows")
print(f"Premium range: ₹{df.annual_premium.min():,} – ₹{df.annual_premium.max():,}")
print(f"Average: ₹{df.annual_premium.mean():,.0f}/year")

X = df[FEATURE_COLUMNS]
y = df["annual_premium"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.1,
    min_samples_split=5,
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2  = r2_score(y_test, y_pred)

print(f"\n✅ MAE: ₹{mae:,.0f}/year")
print(f"✅ R² Score: {r2:.3f}")

print("\n🔍 Feature Importance:")
for feat, imp in sorted(zip(FEATURE_COLUMNS, model.feature_importances_), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"  {feat:<25} {bar} {imp:.3f}")

# Save model + metadata
output = {
    "model": model,
    "feature_columns": FEATURE_COLUMNS,
    "monthly_factor": 1/12,
}
path = os.path.join(os.path.dirname(__file__), "insurance_model.pkl")
with open(path, "wb") as f:
    pickle.dump(output, f)

print(f"\n💾 Saved to: {path}")
print("Now run: uvicorn main:app --reload")