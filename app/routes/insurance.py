from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database import supabase
from app.models.insurance_rules import suggest_insurance, INSURANCE_PLANS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def add_flash(request: Request, category: str, message: str):
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


@router.get("/plans")
async def insurance_plans(
    request:       Request,
    prediction_id: Optional[str] = None,
):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        add_flash(request, "error", "Please login to view insurance plans.")
        return RedirectResponse("/auth/login", status_code=302)

    messages = request.session.pop("messages", [])

    prediction       = None
    risk_level       = "low"
    predicted_disease = "—"
    confidence_score = 0

    pid = prediction_id or request.session.get("latest_prediction_id")

    if pid:
        try:
            res = supabase.table("predictions")\
                .select("risk_level, predicted_disease, confidence_score")\
                .eq("id", pid)\
                .single()\
                .execute()
            prediction = res.data
        except Exception:
            prediction = None

    if not prediction:
        try:
            res = supabase.table("predictions")\
                .select("risk_level, predicted_disease, confidence_score")\
                .eq("patient_id", patient_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            if res.data:
                prediction = res.data[0]
        except Exception:
            prediction = None

    if prediction:
        risk_level        = prediction.get("risk_level", "low")
        predicted_disease = prediction.get("predicted_disease", "—")
        confidence_score  = prediction.get("confidence_score", 0)

    recommended     = suggest_insurance(risk_level)
    recommended_key = recommended["plan_type"]

    return templates.TemplateResponse("insurance.html", {
        "request":              request,
        "messages":             messages,
        "risk_level":           risk_level,
        "predicted_disease":    predicted_disease,
        "confidence_score":     confidence_score,
        "recommended_plan":     recommended_key,
        "recommendation_reason": recommended["reason"],
        "patient_id":           patient_id,
    })


class PlanSelectPayload(BaseModel):
    patient_id: str
    plan_name:  str
    plan_price: str


@router.post("/select")
async def select_plan(payload: PlanSelectPayload):
    try:
        existing = supabase.table("insurance_recommendations")\
            .select("id")\
            .eq("patient_id", payload.patient_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if existing.data:
            record_id = existing.data[0]["id"]
            supabase.table("insurance_recommendations")\
                .update({
                    "plan_name":    payload.plan_name,
                    "monthly_cost": payload.plan_price,
                })\
                .eq("id", record_id)\
                .execute()
        else:
            supabase.table("insurance_recommendations").insert({
                "id":           str(uuid.uuid4()),
                "patient_id":   payload.patient_id,
                "plan_name":    payload.plan_name,
                "monthly_cost": payload.plan_price,
                "plan_type":    "selected",
                "reason":       "Patient manually selected.",
            }).execute()

        return JSONResponse({"status": "ok", "message": "Plan saved successfully."})

    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )
