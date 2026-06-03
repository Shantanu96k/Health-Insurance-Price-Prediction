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

                   
    [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, "Allergy"],
    [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, "Allergy"],
    [0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, "Allergy"],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, "Allergy"],
    [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, "Allergy"],
    [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, "Allergy"],

                        
    [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, "Hypertension"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, "Hypertension"],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, "Hypertension"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, "Hypertension"],
    [0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, "Hypertension"],
    [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, "Hypertension"],

                              
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, "Cancer Risk"],
    [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, "Cancer Risk"],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, "Cancer Risk"],
    [0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, "Cancer Risk"],

                         
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

                                                                         
classes = list(rf_model.classes_)

nb_model.fit(X_train, y_train)

print(f"\n✅ Ensemble Accuracy: {accuracy:.2%}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

                                                                        
print("🔍 Feature Importance (RandomForest):")
for feat, imp in sorted(zip(FEATURE_COLUMNS, rf_model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {feat:<30} {'█' * int(imp * 40)} {imp:.3f}")

                                                                         
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