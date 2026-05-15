# ml/train_model.py
"""
Train the MedPredict ML Model
================================
Run this script ONCE before starting the server:
    python ml/train_model.py

What it does:
  1. Builds a labelled symptom dataset
  2. Trains a RandomForestClassifier
  3. Prints accuracy
  4. Saves model to ml/model.pkl

RandomForest is ideal for this project because:
  - Works well on small tabular datasets
  - Gives a probability/confidence score
  - Easy to explain (100 decision trees, majority vote)
  - Shows which symptom matters most (feature importance)
  - No deep learning complexity
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ── Feature columns — must match FEATURE_COLUMNS in ml_model.py ────────
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

# ── Synthetic training dataset ─────────────────────────────────────────
# Each row = one patient's symptom profile
# In a real project you would use a public medical dataset
# (e.g. UCI Heart Disease Dataset, Pima Indians Diabetes Dataset)
#
# Format: [fever, cough, chest_pain, shortness_of_breath, fatigue,
#          headache, joint_pain, skin_rash, smoker,
#          family_history_diabetes, family_history_heart, disease]

TRAINING_DATA = [
    # Flu cases ─────────────────────────────────────────────────────────
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Flu"],
    [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Flu"],

    # Heart Disease cases ────────────────────────────────────────────────
    [0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, "Heart Disease"],
    [0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, "Heart Disease"],
    [0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, "Heart Disease"],

    # Diabetes Risk cases ────────────────────────────────────────────────
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, "Diabetes Risk"],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, "Diabetes Risk"],

    # Allergy cases ──────────────────────────────────────────────────────
    [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, "Allergy"],
    [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, "Allergy"],
    [0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, "Allergy"],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Allergy"],

    # Hypertension cases ─────────────────────────────────────────────────
    [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, "Hypertension"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, "Hypertension"],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, "Hypertension"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, "Hypertension"],

    # No Significant Risk cases ──────────────────────────────────────────
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, "No Significant Risk"],
]

# ── Build DataFrame ────────────────────────────────────────────────────
columns = FEATURE_COLUMNS + ["disease"]
df = pd.DataFrame(TRAINING_DATA, columns=columns)

print(f"\n📊 Dataset size: {len(df)} rows")
print("Disease distribution:")
print(df["disease"].value_counts())
print()

X = df[FEATURE_COLUMNS]
y = df["disease"]

# ── Train / test split ─────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=None
)

# ── Train RandomForest ─────────────────────────────────────────────────
model = RandomForestClassifier(
    n_estimators=100,       # 100 decision trees
    max_depth=8,            # Prevent overfitting on small dataset
    min_samples_split=2,
    random_state=42,
)
model.fit(X_train, y_train)

# ── Evaluate ───────────────────────────────────────────────────────────
y_pred   = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"✅ Model Accuracy: {accuracy:.2%}")
print()
print("Classification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# ── Feature importance (useful for viva) ───────────────────────────────
print("🔍 Feature Importance (which symptom matters most):")
importances = model.feature_importances_
for feat, imp in sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 40)
    print(f"  {feat:<30} {bar} {imp:.3f}")

# ── Save model ─────────────────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(output_path, "wb") as f:
    pickle.dump(model, f)

print(f"\n💾 Model saved to: {output_path}")
print("Now run: uvicorn main:app --reload")
