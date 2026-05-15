# app/routes/insurance_price.py
"""
Insurance Price Prediction Routes
====================================
Separate from the health form — standalone flow.

Routes:
  GET  /price/form       → Insurance price calculator form
  POST /price/calculate  → Run regression model → show price result
  GET  /price/result     → Price result page (also accessible from dashboard)
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import uuid
import json

from app.database import supabase
from app.models.insurance_price_model import predict_insurance_price
from app.utils.gemini_suggestions import get_insurance_ai_explanation

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_login(request: Request):
    return request.session.get("patient_id")


def add_flash(request: Request, category: str, message: str):
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


# ── GET /price/form ───────────────────────────────────────────────────

@router.get("/form")
async def price_form(request: Request):
    """Standalone insurance price calculator form."""
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login first.")
        return RedirectResponse("/auth/login", status_code=302)

    messages = request.session.pop("messages", [])

    # Pre-fill age/sex from patient record if available
    patient_data = {}
    try:
        res = supabase.table("patient").select("age, gender").eq("id", patient_id).single().execute()
        patient_data = res.data or {}
    except Exception:
        pass

    return templates.TemplateResponse("price_form.html", {
        "request": request,
        "messages": messages,
        "patient_id": patient_id,
        "patient_age": patient_data.get("age", ""),
        "patient_sex": patient_data.get("gender", ""),
    })


# ── POST /price/calculate ─────────────────────────────────────────────

@router.post("/calculate")
async def calculate_price(
    request:          Request,
    patient_id:       str   = Form(...),
    age:              int   = Form(...),
    sex:              str   = Form(...),
    bmi:              float = Form(...),
    children:         int   = Form(...),
    region:           str   = Form(...),
    smoker:           str   = Form(...),
    has_diabetes:     str   = Form(...),
    has_heart:        str   = Form(...),
    has_bp:           str   = Form(...),
    exercise_frequency: str = Form(...),
    diet_quality:     str   = Form(...),
):
    """Calculate insurance premium and save result."""

    form_data = {
        "age":                age,
        "bmi":                bmi,
        "children":           children,
        "region":             region,
        "sex":                sex,
        "smoker":             smoker == "1",
        "has_diabetes":       has_diabetes == "1",
        "has_heart":          has_heart == "1",
        "has_bp":             has_bp == "1",
        "exercise_frequency": exercise_frequency,
        "diet_quality":       diet_quality,
    }

    # Run regression model
    price_result = predict_insurance_price(form_data)

    # Get AI explanation (Gemini or template)
    explanation = get_insurance_ai_explanation(
        price_result["annual_premium"],
        price_result["risk_factors"],
        "General Health Assessment"
    )

    # Save to Supabase
    record_id = str(uuid.uuid4())
    try:
        supabase.table("insurance_price_predictions").insert({
            "id":              record_id,
            "patient_id":      patient_id,
            "age":             age,
            "bmi":             bmi,
            "children":        children,
            "region":          region,
            "sex":             sex,
            "smoker":          smoker == "1",
            "has_diabetes":    has_diabetes == "1",
            "has_heart":       has_heart == "1",
            "has_bp":          has_bp == "1",
            "annual_premium":  price_result["annual_premium"],
            "monthly_premium": price_result["monthly_premium"],
            "premium_band":    price_result["premium_band"],
            "risk_factors":    json.dumps(price_result["risk_factors"]),
        }).execute()
    except Exception as e:
        # Table may not exist yet — don't block the flow
        print(f"DB save skipped: {e}")

    # Store in session for the result page
    request.session["price_result"] = {
        **price_result,
        "explanation": explanation,
        "form_data":   form_data,
        "record_id":   record_id,
    }

    return RedirectResponse("/price/result", status_code=302)


# ── GET /price/result ─────────────────────────────────────────────────

@router.get("/result")
async def price_result(request: Request):
    """Display insurance price prediction result."""
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    result = request.session.get("price_result")
    if not result:
        add_flash(request, "info", "Please fill the insurance calculator form first.")
        return RedirectResponse("/price/form", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("price_result.html", {
        "request":    request,
        "messages":   messages,
        "patient_id": patient_id,
        "result":     result,
        "breakdown":  result.get("breakdown", {}),
    })