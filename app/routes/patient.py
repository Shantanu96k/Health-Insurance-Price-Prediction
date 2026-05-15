# app/routes/patient.py
"""
Patient routes — Health form display, form submission, dashboard.

Routes:
  GET  /patient/dashboard      → Show latest prediction results
  GET  /patient/form           → Show multi-step health questionnaire
  POST /patient/submit-form    → Save form answers + run prediction + redirect to dashboard
"""

from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import uuid
import json

from app.database import supabase
from app.config import settings
from app.models.ml_model import predict_disease
from app.utils.mri_validator import validate_mri_upload
from app.utils.suggestion_engine import get_suggestions
from app.models.insurance_rules import suggest_insurance

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ── Auth guard helper ─────────────────────────────────────────────────

def require_login(request: Request):
    """
    Returns patient_id if logged in, else None.
    Caller should redirect to login if None is returned.
    """
    return request.session.get("patient_id")


def add_flash(request: Request, category: str, message: str):
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


# ── GET /patient/form ─────────────────────────────────────────────────

@router.get("/form")
async def show_form(request: Request):
    """
    Display the multi-step medical history questionnaire.
    Requires the patient to be logged in.
    """
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login to access the health form.")
        return RedirectResponse("/auth/login", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("form.html", {
        "request":    request,
        "patient_id": patient_id,
        "messages":   messages,
    })


# ── POST /patient/submit-form ─────────────────────────────────────────

@router.post("/submit-form")
async def submit_form(
    request:                 Request,
    patient_id:              str  = Form(...),

    # ── Symptoms (checkboxes — value "1" if checked, absent if not)
    fever:                   Optional[str] = Form(None),
    cough:                   Optional[str] = Form(None),
    chest_pain:              Optional[str] = Form(None),
    shortness_of_breath:     Optional[str] = Form(None),
    fatigue:                 Optional[str] = Form(None),
    headache:                Optional[str] = Form(None),
    joint_pain:              Optional[str] = Form(None),
    skin_rash:               Optional[str] = Form(None),
    nausea:                  Optional[str] = Form(None),
    weight_loss:             Optional[str] = Form(None),

    # ── Lifestyle
    smoker:                  str = Form(...),
    alcohol_use:             str = Form(...),
    exercise_frequency:      str = Form(...),
    diet_quality:            str = Form(...),
    blood_pressure:          str = Form(...),
    blood_sugar:             str = Form(...),

    # ── Family history
    family_history_heart:    str = Form(...),
    family_history_diabetes: str = Form(...),
    family_history_cancer:   str = Form(...),

    # ── MRI upload (optional)
    mri_file: Optional[UploadFile] = File(None),
):
    """
    1. Convert all form fields to a clean dict.
    2. If MRI uploaded → read bytes → validate_mri_upload().
    3. Save medical_history row to Supabase.
    4. Run ML prediction (predict_disease).
    5. Get suggestions (get_suggestions).
    6. Save prediction row to Supabase.
    7. Save insurance recommendation to Supabase.
    8. Store latest prediction ID in session → redirect to dashboard.
    """
    # ── 1. Build clean form data dict (all booleans)
    def to_bool(val) -> bool:
        return val == "1"

    form_data = {
        # Symptoms
        "fever":                   to_bool(fever),
        "cough":                   to_bool(cough),
        "chest_pain":              to_bool(chest_pain),
        "shortness_of_breath":     to_bool(shortness_of_breath),
        "fatigue":                 to_bool(fatigue),
        "headache":                to_bool(headache),
        "joint_pain":              to_bool(joint_pain),
        "skin_rash":               to_bool(skin_rash),
        "nausea":                  to_bool(nausea),
        "weight_loss":             to_bool(weight_loss),
        # Lifestyle
        "smoker":                  smoker == "1",
        "alcohol_use":             alcohol_use == "1",
        "exercise_frequency":      exercise_frequency,
        "diet_quality":            diet_quality,
        "blood_pressure":          blood_pressure,
        "blood_sugar":             blood_sugar,
        # Family history
        "family_history_heart":    family_history_heart == "1",
        "family_history_diabetes": family_history_diabetes == "1",
        "family_history_cancer":   family_history_cancer == "1",
    }

    # ── 2. MRI handling
    mri_uploaded   = False
    mri_file_path  = None
    mri_bytes      = None

    if mri_file and mri_file.filename:
        mri_bytes    = await mri_file.read()
        mri_uploaded = True
        # Store filename reference (in a real app: upload to Supabase Storage)
        mri_file_path = f"uploads/{patient_id}/{mri_file.filename}"

    # ── 3. Save medical_history to Supabase
    history_id = str(uuid.uuid4())
    history_row = {
        "id":         history_id,
        "patient_id": patient_id,
        **{k: v for k, v in form_data.items()},
        "mri_uploaded":  mri_uploaded,
        "mri_file_path": mri_file_path,
    }

    try:
        supabase.table("medical_history").insert(history_row).execute()
    except Exception as e:
        add_flash(request, "error", f"Failed to save health data: {str(e)}")
        return RedirectResponse("/patient/form", status_code=302)

    # ── 4. Run ML prediction
    prediction_result = predict_disease(form_data)

    # ── 5. MRI validation (lie detection)
    mri_result = {
        "consistency":  "no_mri",
        "honesty_flag": "trusted",
        "notes":        "No MRI uploaded.",
        "is_valid_image": False,
    }
    if mri_bytes:
        mri_result = validate_mri_upload(mri_bytes, form_data)

    # ── 6. Get health suggestions
    suggestions = get_suggestions(prediction_result["predicted_disease"])

    # ── 7. Save prediction to Supabase
    prediction_id = str(uuid.uuid4())
    pred_row = {
        "id":                prediction_id,
        "patient_id":        patient_id,
        "history_id":        history_id,
        "predicted_disease": prediction_result["predicted_disease"],
        "risk_level":        prediction_result["risk_level"],
        "confidence_score":  prediction_result["confidence_score"],
        "mri_consistency":   mri_result["consistency"],
        "honesty_flag":      mri_result["honesty_flag"],
        "suggestions":       json.dumps(suggestions),
    }

    try:
        supabase.table("predictions").insert(pred_row).execute()
    except Exception as e:
        add_flash(request, "error", f"Failed to save prediction: {str(e)}")
        return RedirectResponse("/patient/form", status_code=302)

    # ── 8. Save insurance recommendation to Supabase
    insurance_plan = suggest_insurance(prediction_result["risk_level"])
    try:
        supabase.table("insurance_recommendations").insert({
            "id":               str(uuid.uuid4()),
            "patient_id":       patient_id,
            "prediction_id":    prediction_id,
            "plan_name":        insurance_plan["plan_name"],
            "plan_type":        insurance_plan["plan_type"],
            "monthly_cost":     insurance_plan["monthly_cost"],
            "coverage_details": json.dumps(insurance_plan["coverage"]),
            "reason":           insurance_plan["reason"],
        }).execute()
    except Exception:
        pass  # Non-critical — don't block the flow if insurance save fails

    # Store prediction_id in session so dashboard can retrieve it
    request.session["latest_prediction_id"] = prediction_id
    add_flash(request, "success", "Health assessment complete! Here are your results.")
    return RedirectResponse("/patient/dashboard", status_code=302)


# ── GET /patient/dashboard ────────────────────────────────────────────

@router.get("/dashboard")
async def dashboard(request: Request):
    """
    Fetch the latest prediction for this patient and render dashboard.
    Falls back gracefully if no prediction exists yet.
    """
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login to view your dashboard.")
        return RedirectResponse("/auth/login", status_code=302)

    messages = request.session.pop("messages", [])

    # Try to get the latest prediction ID from session first
    prediction_id = request.session.get("latest_prediction_id")

    prediction  = None
    suggestions = {"precautions": [], "improvements": []}

    if prediction_id:
        # Fetch by specific prediction ID
        try:
            res = supabase.table("predictions") \
                .select("*") \
                .eq("id", prediction_id) \
                .single() \
                .execute()
            prediction = res.data
        except Exception:
            prediction = None

    if not prediction:
        # Fallback: get the most recent prediction for this patient
        try:
            res = supabase.table("predictions") \
                .select("*") \
                .eq("patient_id", patient_id) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            if res.data:
                prediction = res.data[0]
        except Exception:
            prediction = None

    # Parse suggestions from JSON string stored in DB
    if prediction and prediction.get("suggestions"):
        try:
            suggestions = json.loads(prediction["suggestions"])
        except (json.JSONDecodeError, TypeError):
            suggestions = get_suggestions(prediction.get("predicted_disease", ""))

    # If still no prediction, show empty state
    no_data = prediction is None

    return templates.TemplateResponse("dashboard.html", {
        "request":    request,
        "prediction": prediction or {},
        "suggestions": suggestions,
        "no_data":    no_data,
        "messages":   messages,
    })
