# app/routes/admin.py
"""
Admin Dashboard
================
Simple admin panel for the college project demo.
Shows all patients, recent predictions, and flagged MRI cases.

Routes:
  GET  /admin/          → Admin dashboard overview
  GET  /admin/patients  → All patients list
  GET  /admin/flagged   → Flagged (dishonest) cases

Authentication: Basic password check via session.
In production you'd use a proper admin role system.

Explain in viva:
  "The admin panel lets the hospital administrator view all patient
   assessments, see which patients have flagged MRI inconsistencies,
   and monitor the system's overall usage."
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import os

from app.database import supabase

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def is_admin(request: Request) -> bool:
    return request.session.get("is_admin", False)


def add_flash(request: Request, cat: str, msg: str):
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((cat, msg))


# ── GET /admin/login ──────────────────────────────────────────────────

@router.get("/login")
async def admin_login_page(request: Request):
    if is_admin(request):
        return RedirectResponse("/admin/", status_code=302)
    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_login.html", {
        "request": request, "messages": messages
    })


@router.post("/login")
async def admin_login_submit(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse("/admin/", status_code=302)
    add_flash(request, "error", "Incorrect admin password.")
    return RedirectResponse("/admin/login", status_code=302)


@router.get("/logout")
async def admin_logout(request: Request):
    request.session.pop("is_admin", None)
    return RedirectResponse("/admin/login", status_code=302)


# ── GET /admin/ ───────────────────────────────────────────────────────

@router.get("/")
async def admin_dashboard(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=302)

    # Stats
    try:
        total_patients  = len(supabase.table("patient").select("id").execute().data or [])
        total_preds     = len(supabase.table("predictions").select("id").execute().data or [])
        flagged         = supabase.table("predictions").select("id").eq("honesty_flag", "review_needed").execute()
        flagged_count   = len(flagged.data or [])

        # Recent predictions
        recent = supabase.table("predictions") \
            .select("id, patient_id, predicted_disease, risk_level, confidence_score, honesty_flag, created_at") \
            .order("created_at", desc=True).limit(10).execute()
        recent_preds = recent.data or []

        # Risk distribution
        all_preds = supabase.table("predictions").select("risk_level").execute().data or []
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        for p in all_preds:
            risk_dist[p.get("risk_level", "low")] = risk_dist.get(p.get("risk_level", "low"), 0) + 1

        # Disease distribution
        disease_counts = {}
        for p in all_preds:
            d = supabase.table("predictions").select("predicted_disease").execute().data or []
        all_full = supabase.table("predictions").select("predicted_disease").execute().data or []
        for p in all_full:
            dis = p.get("predicted_disease", "Unknown")
            disease_counts[dis] = disease_counts.get(dis, 0) + 1

    except Exception as e:
        total_patients = total_preds = flagged_count = 0
        recent_preds = []
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        disease_counts = {}

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_dashboard.html", {
        "request":        request,
        "messages":       messages,
        "total_patients": total_patients,
        "total_preds":    total_preds,
        "flagged_count":  flagged_count,
        "recent_preds":   recent_preds,
        "risk_dist":      risk_dist,
        "disease_counts": disease_counts,
    })


# ── GET /admin/patients ───────────────────────────────────────────────

@router.get("/patients")
async def admin_patients(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=302)

    try:
        patients = supabase.table("patient") \
            .select("id, full_name, email, age, gender, created_at") \
            .order("created_at", desc=True).execute().data or []
    except Exception:
        patients = []

    return templates.TemplateResponse("admin_patients.html", {
        "request": request, "patients": patients
    })


# ── GET /admin/flagged ────────────────────────────────────────────────

@router.get("/flagged")
async def admin_flagged(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=302)

    try:
        flagged = supabase.table("predictions") \
            .select("id, patient_id, predicted_disease, risk_level, mri_consistency, honesty_flag, created_at") \
            .eq("honesty_flag", "review_needed") \
            .order("created_at", desc=True).execute().data or []
    except Exception:
        flagged = []

    return templates.TemplateResponse("admin_flagged.html", {
        "request": request, "flagged": flagged
    })