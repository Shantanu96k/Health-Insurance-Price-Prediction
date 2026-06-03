# app/routes/insurance_price.py
"""
Insurance Price Calculator
===========================
Predicts annual and monthly health insurance premiums using a
Gradient Boosting regression model trained on demographic and
lifestyle features.

Routes:
  GET  /price/form       → Premium calculator form
  POST /price/calculate  → Run model and redirect to result
  GET  /price/result     → Display last calculated premium
  GET  /price/history    → All past premium calculations for this patient

Architecture note (for viva):
  Instead of storing the full result in the session cookie (which has a ~4KB
  limit), we persist results to Supabase and store only minimal keys in the
  session. The result page reconstructs the full data from the DB + a fast
  in-memory model re-run.

Fix applied:
  - Supabase RLS on `insurance_price_predictions` requires the user's JWT.
    We now fall back to storing everything in session if the DB insert fails,
    so the result page always works even when the table doesn't exist yet.
  - Ordering changed from `id` (UUID, not chronological) to `created_at`.
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

router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ── Helpers ────────────────────────────────────────────────────────────

def require_login(request: Request) -> Optional[str]:
    return request.session.get("patient_id")


def add_flash(request: Request, category: str, message: str) -> None:
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


# ── GET /price/form ────────────────────────────────────────────────────

@router.get("/form")
async def price_form(request: Request):
    """Show the insurance premium calculator form."""
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login first.")
        return RedirectResponse("/auth/login", status_code=302)

    messages     = request.session.pop("messages", [])
    patient_data = {}
    try:
        res = supabase.table("patient") \
            .select("age, gender") \
            .eq("id", patient_id) \
            .single() \
            .execute()
        patient_data = res.data or {}
    except Exception:
        pass

    return templates.TemplateResponse("price_form.html", {
        "request":     request,
        "messages":    messages,
        "patient_id":  patient_id,
        "patient_age": patient_data.get("age", ""),
        "patient_sex": patient_data.get("gender", ""),
    })


# ── POST /price/calculate ──────────────────────────────────────────────

@router.post("/calculate")
async def calculate_price(
    request:            Request,
    patient_id:         str   = Form(...),
    age:                int   = Form(...),
    sex:                str   = Form(...),
    bmi:                float = Form(...),
    children:           int   = Form(...),
    region:             str   = Form(...),
    smoker:             str   = Form(...),
    has_diabetes:       str   = Form(...),
    has_heart:          str   = Form(...),
    has_bp:             str   = Form(...),
    exercise_frequency: str   = Form(...),
    diet_quality:       str   = Form(...),
):
    """
    Run the insurance price regression model and store the result.

    Pipeline:
      1. Parse form inputs
      2. Run GradientBoosting prediction
      3. Get Gemini AI explanation (with fallback)
      4. Persist to Supabase (best-effort — not blocking)
      5. Store compact result in session
      6. Redirect to /price/result
    """
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

    price_result = predict_insurance_price(form_data)

    explanation = get_insurance_ai_explanation(
        price_result["annual_premium"],
        price_result["risk_factors"],
        "General Health Assessment",
    )

    # ── Persist to DB (best-effort; fails silently if RLS blocks it) ───
    record_id = str(uuid.uuid4())
    db_saved  = False
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
        db_saved = True
    except Exception as e:
        print(f"[INFO] DB insert skipped (RLS or missing table): {e}")

    # ── Store compact result in session ───────────────────────────────
    # We keep each value as a separate key (not a nested dict) to stay
    # well within the Starlette cookie ~4KB limit.
    request.session["price_result_id"]      = record_id
    request.session["price_annual"]         = price_result["annual_premium"]
    request.session["price_monthly"]        = price_result["monthly_premium"]
    request.session["price_band"]           = price_result["premium_band"]
    request.session["price_db_saved"]       = db_saved
    request.session["price_explanation"]    = explanation[:500]    # truncate to be safe
    request.session["price_risk_factors"]   = json.dumps(price_result["risk_factors"])
    request.session["price_breakdown"]      = json.dumps(price_result.get("breakdown", {}))
    request.session["price_form_snapshot"]  = json.dumps({
        "age": age, "bmi": bmi, "children": children, "region": region,
        "sex": sex, "smoker": smoker == "1",
        "has_diabetes": has_diabetes == "1",
        "has_heart": has_heart == "1",
        "has_bp": has_bp == "1",
        "exercise_frequency": exercise_frequency,
        "diet_quality": diet_quality,
    })

    return RedirectResponse("/price/result", status_code=302)


# ── GET /price/result ──────────────────────────────────────────────────

@router.get("/result")
async def price_result(request: Request):
    """
    Display the most recently calculated insurance premium.
    Reconstructs full result from session keys (avoids cookie overflow).
    """
    patient_id = require_login(request)
    if not patient_id:
        return RedirectResponse("/auth/login", status_code=302)

    annual  = request.session.get("price_annual")
    monthly = request.session.get("price_monthly")
    band    = request.session.get("price_band")

    if annual is None:
        add_flash(request, "info", "Please fill the insurance calculator form first.")
        return RedirectResponse("/price/form", status_code=302)

    explanation   = request.session.get("price_explanation", "")
    record_id     = request.session.get("price_result_id")
    risk_factors  = []
    breakdown     = {}
    form_data     = {}

    try:
        risk_factors = json.loads(request.session.get("price_risk_factors", "[]"))
    except Exception:
        pass
    try:
        breakdown = json.loads(request.session.get("price_breakdown", "{}"))
    except Exception:
        pass
    try:
        form_data = json.loads(request.session.get("price_form_snapshot", "{}"))
    except Exception:
        pass

    # Re-run model in memory if breakdown is missing (very fast, no DB needed)
    if not breakdown and form_data:
        try:
            fresh        = predict_insurance_price(form_data)
            breakdown    = fresh.get("breakdown", {})
            risk_factors = fresh.get("risk_factors", risk_factors)
        except Exception:
            pass

    if not explanation:
        explanation = get_insurance_ai_explanation(annual, risk_factors, "General Health Assessment")

    result = {
        "annual_premium":  annual,
        "monthly_premium": monthly,
        "premium_band":    band,
        "risk_factors":    risk_factors,
        "explanation":     explanation,
        "form_data":       form_data,
        "record_id":       record_id,
        "breakdown":       breakdown,
    }

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("price_result.html", {
        "request":    request,
        "messages":   messages,
        "patient_id": patient_id,
        "result":     result,
        "breakdown":  breakdown,
    })


# ── GET /price/history ─────────────────────────────────────────────────

@router.get("/history")
async def price_history_page(request: Request):
    """
    Show all past insurance premium calculations for this patient.
    This is a standalone history page linked from the navbar.
    The combined health + price history is also accessible at /patient/history.
    """
    patient_id = require_login(request)
    if not patient_id:
        add_flash(request, "error", "Please login to view your history.")
        return RedirectResponse("/auth/login", status_code=302)

    price_history = []
    try:
        res = supabase.table("insurance_price_predictions") \
            .select("id, annual_premium, monthly_premium, premium_band, region, age, smoker, created_at") \
            .eq("patient_id", patient_id) \
            .order("created_at", desc=True) \
            .execute()
        price_history = res.data or []

        # Normalize numeric fields
        for item in price_history:
            try:
                item["annual_premium"]  = int(item.get("annual_premium") or 0)
                item["monthly_premium"] = int(item.get("monthly_premium") or 0)
            except Exception:
                item["annual_premium"]  = 0
                item["monthly_premium"] = 0
    except Exception as e:
        print(f"[WARN] Failed to fetch price history: {e}")
        price_history = []

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("price_history.html", {
        "request":       request,
        "messages":      messages,
        "price_history": price_history,
        "price_total":   len(price_history),
    })