# app/routes/patient.py
"""
Patient routes — Health form, submission, dashboard, history, settings.

Routes:
  GET  /patient/dashboard             → Latest prediction results + Health Score + Doctor Alert
  GET  /patient/form                  → Multi-step health questionnaire
  POST /patient/submit-form           → Save + predict + redirect to dashboard
  GET  /patient/history               → All past predictions for this patient
  GET  /patient/history/{id}          → Single prediction detail
  GET  /patient/settings              → Patient settings page
  POST /patient/settings              → Update patient settings
  GET  /patient/api/trend             → JSON: risk trend data for Chart.js [NEW]
  GET  /patient/report/{pred_id}      → PDF health report download [NEW]

New in v2.1:
  - Health Score (0-100 wellness index) computed on every dashboard load
  - Trend data API endpoint for Chart.js line chart
  - PDF report download via ReportLab
  - Doctor alert card generated for high-risk patients via Gemini
"""

from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Optional
import uuid
import json
from datetime import datetime

from app.database import supabase
from app.config import settings
from app.models.ml_model import predict_disease, calculate_health_score
from app.utils.mri_validator import validate_mri_upload
from app.utils.suggestion_engine import get_suggestions
from app.utils.ai_health_tips import get_ai_health_tips
from app.models.insurance_rules import suggest_insurance

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ── Auth guard ────────────────────────────────────────────────────────

def require_login(request: Request):
    return request.session.get("patient_id")


def add_flash(request: Request, category: str, message: str):
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


# ── GET /patient/form ─────────────────────────────────────────────────

@router.get("/form")
async def show_form(request: Request):
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

    # Symptoms
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

    # Lifestyle
    smoker:                  str = Form(...),
    alcohol_use:             str = Form(...),
    exercise_frequency:      str = Form(...),
    diet_quality:            str = Form(...),
    blood_pressure:          str = Form(...),
    blood_sugar:             str = Form(...),

    # Family history
    family_history_heart:    str = Form(...),
    family_history_diabetes: str = Form(...),
    family_history_cancer:   str = Form(...),

    # MRI upload (optional)
    mri_file: Optional[UploadFile] = File(None),
):
    """
    Full pipeline:
    1. Parse form data
    2. Validate MRI if uploaded
    3. Save medical_history to Supabase
    4. Run ML prediction (Ensemble)
    5. Calculate Health Score
    6. Get AI health tips
    7. Get suggestions
    8. Save prediction to Supabase
    9. Save insurance recommendation
    10. Redirect to dashboard
    """

    def to_bool(val) -> bool:
        return val == "1"

    form_data = {
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
        "smoker":                  smoker == "1",
        "alcohol_use":             alcohol_use == "1",
        "exercise_frequency":      exercise_frequency,
        "diet_quality":            diet_quality,
        "blood_pressure":          blood_pressure,
        "blood_sugar":             blood_sugar,
        "family_history_heart":    family_history_heart == "1",
        "family_history_diabetes": family_history_diabetes == "1",
        "family_history_cancer":   family_history_cancer == "1",
    }

    # ── MRI handling ──────────────────────────────────────────────────
    mri_uploaded  = False
    mri_file_path = None
    mri_bytes     = None

    if mri_file and mri_file.filename:
        mri_bytes     = await mri_file.read()
        mri_uploaded  = True
        mri_file_path = f"uploads/{patient_id}/{mri_file.filename}"

    # ── Save medical_history ──────────────────────────────────────────
    history_id  = str(uuid.uuid4())
    history_row = {
        "id":            history_id,
        "patient_id":    patient_id,
        **{k: v for k, v in form_data.items()},
        "mri_uploaded":  mri_uploaded,
        "mri_file_path": mri_file_path,
    }

    try:
        supabase.table("medical_history").insert(history_row).execute()
    except Exception as e:
        add_flash(request, "error", f"Failed to save health data: {str(e)}")
        return RedirectResponse("/patient/form", status_code=302)

    # ── ML prediction ─────────────────────────────────────────────────
    prediction_result = predict_disease(form_data)

    # ── Health Score ──────────────────────────────────────────────────
    health_score = calculate_health_score(prediction_result, form_data)

    # ── MRI validation ────────────────────────────────────────────────
    mri_result = {
        "consistency":    "no_mri",
        "honesty_flag":   "trusted",
        "notes":          "No MRI uploaded.",
        "is_valid_image": False,
    }
    if mri_bytes:
        mri_result = validate_mri_upload(mri_bytes, form_data)

    # ── Health suggestions ────────────────────────────────────────────
    suggestions = get_suggestions(prediction_result["predicted_disease"])

    # ── AI Health Tips ────────────────────────────────────────────────
    try:
        ai_tips = get_ai_health_tips(prediction_result, form_data)
    except Exception:
        ai_tips = {"do": [], "dont": [], "improve": [], "diet": [], "exercise": []}

    # ── Save prediction ───────────────────────────────────────────────
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
        "ai_tips":           json.dumps(ai_tips),
        "form_snapshot":     json.dumps(form_data),
        "health_score":      health_score["score"],
    }

    try:
        supabase.table("predictions").insert(pred_row).execute()
    except Exception as e:
        add_flash(request, "error", f"Failed to save prediction: {str(e)}")
        return RedirectResponse("/patient/form", status_code=302)

    # ── Insurance recommendation ──────────────────────────────────────
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
        pass

    request.session["latest_prediction_id"] = prediction_id
    add_flash(request, "success", "Health assessment complete! Here are your results.")
    return RedirectResponse("/patient/dashboard", status_code=302)


# ── GET /patient/dashboard ────────────────────────────────────────────

@router.get("/dashboard")
async def dashboard(request: Request):
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login to view your dashboard.")
        return RedirectResponse("/auth/login", status_code=302)

    messages      = request.session.pop("messages", [])
    prediction_id = request.session.get("latest_prediction_id")

    prediction  = None
    suggestions = {"precautions": [], "improvements": []}
    ai_tips     = {"do": [], "dont": [], "improve": [], "diet": [], "exercise": []}

    if prediction_id:
        try:
            res = supabase.table("predictions") \
                .select("*").eq("id", prediction_id).single().execute()
            prediction = res.data
        except Exception:
            prediction = None

    if not prediction:
        try:
            res = supabase.table("predictions") \
                .select("*").eq("patient_id", patient_id) \
                .order("created_at", desc=True).limit(1).execute()
            if res.data:
                prediction = res.data[0]
        except Exception:
            prediction = None

    if prediction:
        try:
            suggestions = json.loads(prediction.get("suggestions", "{}"))
        except Exception:
            suggestions = get_suggestions(prediction.get("predicted_disease", ""))

        try:
            ai_tips = json.loads(prediction.get("ai_tips", "{}"))
        except Exception:
            ai_tips = {"do": [], "dont": [], "improve": [], "diet": [], "exercise": []}

    # ── Health Score ──────────────────────────────────────────────────
    health_score = None
    if prediction:
        # Try DB-stored score first, compute if not available
        stored_score = prediction.get("health_score")
        if stored_score is not None:
            # Reconstruct full health_score dict from score value
            from app.models.ml_model import calculate_health_score
            try:
                form_snap = json.loads(prediction.get("form_snapshot", "{}"))
                health_score = calculate_health_score(
                    {"predicted_disease": prediction.get("predicted_disease", ""),
                     "risk_level": prediction.get("risk_level", "low"),
                     "confidence_score": prediction.get("confidence_score", 50)},
                    form_snap
                )
            except Exception:
                health_score = {"score": stored_score, "grade": "—", "label": "—", "color": "#64748b", "breakdown": {}}
        else:
            try:
                form_snap = json.loads(prediction.get("form_snapshot", "{}"))
                health_score = calculate_health_score(
                    {"predicted_disease": prediction.get("predicted_disease", ""),
                     "risk_level": prediction.get("risk_level", "low"),
                     "confidence_score": prediction.get("confidence_score", 50)},
                    form_snap
                )
            except Exception:
                health_score = None

    # ── Doctor Alert for HIGH RISK ─────────────────────────────────────
    doctor_alert = None
    if prediction and prediction.get("risk_level") == "high":
        try:
            disease    = prediction.get("predicted_disease", "Unknown")
            confidence = prediction.get("confidence_score", 0)
            form_snap  = json.loads(prediction.get("form_snapshot", "{}"))

            # Build a concise doctor-ready summary
            risk_factors = []
            if form_snap.get("smoker"):               risk_factors.append("Smoker")
            if form_snap.get("alcohol_use"):           risk_factors.append("Alcohol use")
            if form_snap.get("blood_pressure") == "high": risk_factors.append("High BP")
            if form_snap.get("blood_sugar") == "high":    risk_factors.append("High blood sugar")
            if form_snap.get("family_history_heart"):  risk_factors.append("Family history: Heart disease")
            if form_snap.get("family_history_diabetes"): risk_factors.append("Family history: Diabetes")
            if form_snap.get("family_history_cancer"):   risk_factors.append("Family history: Cancer")

            subject   = f"High Risk Health Alert — {disease} (MedPredict)"
            body_text = (
                f"Dear Doctor,\n\n"
                f"My recent AI health assessment flagged a HIGH RISK result.\n\n"
                f"Predicted Condition: {disease}\n"
                f"Confidence: {confidence}%\n"
                f"Risk Level: HIGH\n"
                f"Health Score: {health_score['score'] if health_score else 'N/A'}/100\n"
            )
            if risk_factors:
                body_text += f"Key Risk Factors: {', '.join(risk_factors)}\n"
            body_text += (
                f"\nThis was generated by MedPredict AI for educational purposes.\n"
                f"I would like to schedule an appointment for a clinical review.\n\n"
                f"Thank you."
            )
            import urllib.parse
            doctor_alert = {
                "disease":      disease,
                "confidence":   confidence,
                "risk_factors": risk_factors,
                "mailto_link":  f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body_text)}",
                "summary_text": body_text,
            }
        except Exception:
            doctor_alert = None

    # ── Count total predictions ────────────────────────────────────────
    total_predictions = 0
    try:
        res = supabase.table("predictions").select("id", count="exact") \
            .eq("patient_id", patient_id).execute()
        total_predictions = res.count or 0
    except Exception:
        pass

    return templates.TemplateResponse("dashboard.html", {
        "request":           request,
        "prediction":        prediction or {},
        "suggestions":       suggestions,
        "ai_tips":           ai_tips,
        "no_data":           prediction is None,
        "messages":          messages,
        "total_predictions": total_predictions,
        "health_score":      health_score,
        "doctor_alert":      doctor_alert,
    })


# ── GET /patient/history ──────────────────────────────────────────────

@router.get("/history")
async def prediction_history(request: Request):
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login.")
        return RedirectResponse("/auth/login", status_code=302)

    predictions = []
    try:
        res = supabase.table("predictions") \
            .select("id, predicted_disease, risk_level, confidence_score, honesty_flag, mri_consistency, health_score, created_at") \
            .eq("patient_id", patient_id) \
            .order("created_at", desc=True) \
            .execute()
        predictions = res.data or []
    except Exception:
        predictions = []

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("history.html", {
        "request":     request,
        "predictions": predictions,
        "messages":    messages,
        "total":       len(predictions),
    })


# ── GET /patient/history/{prediction_id} ──────────────────────────────

@router.get("/history/{prediction_id}")
async def history_detail(request: Request, prediction_id: str):
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    prediction  = None
    suggestions = {"precautions": [], "improvements": []}
    ai_tips     = {}
    form_data   = {}

    try:
        res = supabase.table("predictions") \
            .select("*").eq("id", prediction_id) \
            .eq("patient_id", patient_id).single().execute()
        prediction = res.data
    except Exception:
        pass

    if not prediction:
        add_flash(request, "error", "Prediction not found.")
        return RedirectResponse("/patient/history", status_code=302)

    try:
        suggestions = json.loads(prediction.get("suggestions", "{}"))
    except Exception:
        pass
    try:
        ai_tips = json.loads(prediction.get("ai_tips", "{}"))
    except Exception:
        pass
    try:
        form_data = json.loads(prediction.get("form_snapshot", "{}"))
    except Exception:
        pass

    return templates.TemplateResponse("history_detail.html", {
        "request":    request,
        "prediction": prediction,
        "suggestions": suggestions,
        "ai_tips":    ai_tips,
        "form_data":  form_data,
        "messages":   [],
    })


# ── GET /patient/settings ─────────────────────────────────────────────

@router.get("/settings")
async def settings_page(request: Request):
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    patient = {}
    try:
        res = supabase.table("patient") \
            .select("*").eq("id", patient_id).single().execute()
        patient = res.data or {}
    except Exception:
        pass

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("settings.html", {
        "request":  request,
        "patient":  patient,
        "messages": messages,
    })


# ── POST /patient/settings ────────────────────────────────────────────

@router.post("/settings")
async def update_settings(
    request:      Request,
    full_name:    str = Form(...),
    age:          int = Form(...),
    gender:       str = Form(...),
    phone:        Optional[str] = Form(None),
    city:         Optional[str] = Form(None),
    blood_group:  Optional[str] = Form(None),
    emergency_contact: Optional[str] = Form(None),
    notifications_email: Optional[str] = Form(None),
):
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    update_data = {
        "full_name":            full_name.strip(),
        "age":                  age,
        "gender":               gender,
        "phone":                phone,
        "city":                 city,
        "blood_group":          blood_group,
        "emergency_contact":    emergency_contact,
        "notifications_email":  notifications_email == "on",
    }

    try:
        supabase.table("patient").update(update_data).eq("id", patient_id).execute()
        request.session["patient_name"] = full_name.strip()
        add_flash(request, "success", "Settings updated successfully!")
    except Exception as e:
        add_flash(request, "error", f"Failed to update settings: {str(e)}")

    return RedirectResponse("/patient/settings", status_code=302)


# ── POST /patient/delete-account ─────────────────────────────────────

@router.post("/delete-account")
async def delete_account(request: Request, confirm_delete: str = Form(...)):
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    if confirm_delete != "DELETE":
        add_flash(request, "error", "Type DELETE to confirm account deletion.")
        return RedirectResponse("/patient/settings", status_code=302)

    try:
        supabase.table("predictions").delete().eq("patient_id", patient_id).execute()
        supabase.table("medical_history").delete().eq("patient_id", patient_id).execute()
        supabase.table("insurance_recommendations").delete().eq("patient_id", patient_id).execute()
        supabase.table("patient").delete().eq("id", patient_id).execute()
        request.session.clear()
        return RedirectResponse("/auth/register", status_code=302)
    except Exception as e:
        add_flash(request, "error", f"Deletion failed: {str(e)}")
        return RedirectResponse("/patient/settings", status_code=302)


# ── GET /patient/api/trend ────────────────────────────────────────────
# NEW — Phase 3: Trend Chart Data

@router.get("/api/trend")
async def api_trend(request: Request):
    """
    Returns JSON data for the health trend Chart.js line chart.
    Shows risk level and health score over the last 10 assessments.

    Explain in viva:
      "This API endpoint returns historical assessment data as JSON.
       The dashboard Chart.js chart calls it on load to draw the health
       trend line — showing whether the patient is improving over time."
    """
    patient_id = require_login(request)
    if not patient_id:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    try:
        res = supabase.table("predictions") \
            .select("predicted_disease, risk_level, confidence_score, health_score, created_at") \
            .eq("patient_id", patient_id) \
            .order("created_at", desc=False) \
            .limit(10).execute()
        preds = res.data or []
    except Exception:
        return JSONResponse({"labels": [], "scores": [], "risk": []})

    risk_map = {"low": 25, "medium": 55, "high": 85}

    labels  = []
    scores  = []
    risks   = []
    diseases= []

    for p in preds:
        date_str = p.get("created_at", "")[:10] if p.get("created_at") else "—"
        labels.append(date_str)
        scores.append(p.get("health_score") or 50)
        risks.append(risk_map.get(p.get("risk_level", "low"), 25))
        diseases.append(p.get("predicted_disease", "Unknown"))

    return JSONResponse({
        "labels":   labels,
        "scores":   scores,
        "risks":    risks,
        "diseases": diseases,
    })


# ── GET /patient/report/{prediction_id} ───────────────────────────────
# NEW — Phase 4: PDF Download

@router.get("/report/{prediction_id}")
async def download_report(request: Request, prediction_id: str):
    """
    Generate and stream a PDF health report for a specific prediction.

    Explain in viva:
      "The patient can download a professional PDF summary of their assessment.
       It's generated server-side using ReportLab and streamed as a file download.
       This is something a patient can physically share with their doctor."
    """
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    # Fetch prediction
    try:
        res = supabase.table("predictions") \
            .select("*").eq("id", prediction_id) \
            .eq("patient_id", patient_id).single().execute()
        prediction = res.data
    except Exception:
        prediction = None

    if not prediction:
        add_flash(request, "error", "Report not found.")
        return RedirectResponse("/patient/history", status_code=302)

    # Fetch patient name
    patient_name = request.session.get("patient_name", "Patient")

    # Parse ai_tips and form_snapshot
    try:
        ai_tips = json.loads(prediction.get("ai_tips", "{}"))
    except Exception:
        ai_tips = {}

    try:
        form_snap = json.loads(prediction.get("form_snapshot", "{}"))
    except Exception:
        form_snap = {}

    # Compute health score
    try:
        from app.models.ml_model import calculate_health_score
        health_score = calculate_health_score(
            {"predicted_disease": prediction.get("predicted_disease", ""),
             "risk_level":        prediction.get("risk_level", "low"),
             "confidence_score":  prediction.get("confidence_score", 50)},
            form_snap
        )
    except Exception:
        health_score = None

    # Fetch insurance plan
    insurance_plan = None
    try:
        ins_res = supabase.table("insurance_recommendations") \
            .select("plan_name, plan_type, monthly_cost") \
            .eq("prediction_id", prediction_id).limit(1).execute()
        if ins_res.data:
            insurance_plan = ins_res.data[0]
    except Exception:
        pass

    # Generate PDF bytes
    from app.utils.pdf_generator import generate_health_report_pdf
    pdf_bytes = generate_health_report_pdf(
        patient_name  = patient_name,
        prediction    = prediction,
        ai_tips       = ai_tips,
        health_score  = health_score,
        insurance_plan= insurance_plan,
    )

    filename = f"MedPredict_Report_{prediction_id[:8]}.pdf"
    return Response(
        content     = pdf_bytes,
        media_type  = "application/pdf",
        headers     = {"Content-Disposition": f'attachment; filename="{filename}"'},
    )