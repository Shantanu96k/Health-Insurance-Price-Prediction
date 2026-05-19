# ml/train_model.py
"""
Train Ensemble ML Model
========================
Trains 3 models and saves as a soft-voting ensemble:
  1. RandomForestClassifier   — robust, handles small datasets well
  2. GradientBoostingClassifier — boosting improves edge cases
  3. GaussianNaiveBayes       — probabilistic baseline

Why ensemble?
  - Single models overfit on small datasets
  - Averaging probabilities gives more stable predictions
  - Each model captures different patterns

Post-Graduate Level explanation:
  "Soft voting ensemble combines class probability vectors from multiple
   base classifiers and averages them. The class with highest average
   probability wins. This reduces variance and improves reliability
   without complex hyperparameter tuning."

Run:
    python ml/train_model.py
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

FEATURE_COLUMNS = [
    "fever", "cough", "chest_pain", "shortness_of_breath", "fatigue",
    "headache", "joint_pain", "skin_rash", "smoker",
    "family_history_diabetes", "family_history_heart",
]

TRAINING_DATA = [
    # Flu cases
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Flu"],
    [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, "Flu"],
    [0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, "Flu"],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "Flu"],

    # Heart Disease cases
    [0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, "Heart Disease"],
    [0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, "Heart Disease"],
    [0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, "Heart Disease"],
    [0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, "Heart Disease"],
    [0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, "Heart Disease"],
    [1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, "Heart Disease"],
    [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, "Heart Disease"],

    # Diabetes Risk cases
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, "Diabetes Risk"],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, "Diabetes Risk"],
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, "Diabetes Risk"],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, "Diabetes Risk"],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, "Diabetes Risk"],

    # Allergy cases
    [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, "Allergy"],
    [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, "Allergy"],
    [0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, "Allergy"],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, "Allergy"],

    # Hypertension cases
    [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, "Hypertension"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, "Hypertension"],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, "Hypertension"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, "Hypertension"],
    [0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, "Hypertension"],
    [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, "Hypertension"],

    # Cancer Risk cases (new!)
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, "Cancer Risk"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, "Cancer Risk"],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, "Cancer Risk"],
    [0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, "Cancer Risk"],

    # No Significant Risk
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, "No Significant Risk"],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "No Significant Risk"],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "No Significant Risk"],
]

columns = FEATURE_COLUMNS + ["disease"]
df      = pd.DataFrame(TRAINING_DATA, columns=columns)

print(f"\n📊 Dataset: {len(df)} rows")
print("Disease distribution:")
print(df["disease"].value_counts())
print()

X = df[FEATURE_COLUMNS]
y = df["disease"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

# ── Train 3 base models ────────────────────────────────────────────────
rf_model = RandomForestClassifier(
    n_estimators=200, max_depth=8, min_samples_split=2, random_state=42
)
gb_model = GradientBoostingClassifier(
    n_estimators=150, max_depth=4, learning_rate=0.1, random_state=42
)
nb_model = GaussianNB()

print("Training RandomForest...   ", end="")
rf_model.fit(X_train, y_train)
print(f"Done. CV: {cross_val_score(rf_model, X, y, cv=3).mean():.2%}")

print("Training GradientBoosting..", end="")
gb_model.fit(X_train, y_train)
print(f"Done. CV: {cross_val_score(gb_model, X, y, cv=3).mean():.2%}")

print("Training NaiveBayes...     ", end="")
nb_model.fit(X_train, y_train)
print(f"Done. CV: {cross_val_score(nb_model, X, y, cv=3).mean():.2%}")

# ── Ensemble evaluation ────────────────────────────────────────────────
classes = list(rf_model.classes_)

def ensemble_predict(X_test_data):
    proba_sum = np.zeros((len(X_test_data), len(classes)))
    for m in [rf_model, gb_model, nb_model]:
        proba_sum += m.predict_proba(X_test_data)
    avg = proba_sum / 3
    return [classes[i] for i in np.argmax(avg, axis=1)]

y_pred    = ensemble_predict(X_test)
accuracy  = accuracy_score(y_test, y_pred)

print(f"\n✅ Ensemble Accuracy: {accuracy:.2%}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# ── Feature importance (from RF) ──────────────────────────────────────
print("🔍 Feature Importance (RandomForest):")
for feat, imp in sorted(zip(FEATURE_COLUMNS, rf_model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {feat:<30} {'█' * int(imp * 40)} {imp:.3f}")

# ── Save ensemble ──────────────────────────────────────────────────────
output = {
    "models":  [rf_model, gb_model, nb_model],
    "classes": classes,
    "feature_columns": FEATURE_COLUMNS,
    "model_names": ["RandomForest", "GradientBoosting", "NaiveBayes"],
}

path = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(path, "wb") as f:
    pickle.dump(output, f)

print(f"\n💾 Ensemble saved to: {path}")
print("Now run: uvicorn main:app --reload")