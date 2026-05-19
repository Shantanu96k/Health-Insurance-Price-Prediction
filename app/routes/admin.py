# app/routes/admin.py
"""
Admin Dashboard
================
Shows all patients, recent predictions, and flagged MRI cases.

Routes:
  GET  /admin/          → Admin dashboard overview (with Chart.js analytics)
  GET  /admin/patients  → All patients list
  GET  /admin/flagged   → Flagged (dishonest) cases

Bug Fix: Removed N+1 query loop — now fetches all data in one query.
New: Disease & Risk distribution data passed for Chart.js charts.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from collections import defaultdict
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

@router.get("")
async def admin_redirect():
    """Redirect /admin to /admin/ to fix missing trailing slash issues."""
    return RedirectResponse("/admin/", status_code=307)

@router.get("/")
async def admin_dashboard(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=302)

    try:
        # ── Single query for all predictions (fixes N+1 bug) ───────────
        all_preds_res = supabase.table("predictions") \
            .select("id, patient_id, predicted_disease, risk_level, confidence_score, honesty_flag, created_at") \
            .order("created_at", desc=True).execute()
        all_preds = all_preds_res.data or []

        total_preds    = len(all_preds)
        recent_preds   = all_preds[:10]                      # Top 10 most recent
        flagged_count  = sum(1 for p in all_preds if p.get("honesty_flag") == "review_needed")

        # ── Patient count (one separate query, not N queries) ──────────
        patients_res   = supabase.table("patient").select("id").execute()
        total_patients = len(patients_res.data or [])

        # ── Risk distribution (Python aggregation, zero extra queries) ──
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        for p in all_preds:
            rl = p.get("risk_level", "low")
            risk_dist[rl] = risk_dist.get(rl, 0) + 1

        # ── Disease distribution (same single query result) ─────────────
        disease_counts: dict = defaultdict(int)
        for p in all_preds:
            dis = p.get("predicted_disease") or "Unknown"
            disease_counts[dis] += 1
        disease_counts = dict(disease_counts)

        # ── Monthly patient registrations ──────────────────────────────
        all_patients_res = supabase.table("patient").select("created_at").execute()
        monthly_counts: dict = defaultdict(int)
        for pt in (all_patients_res.data or []):
            if pt.get("created_at"):
                month_key = pt["created_at"][:7]   # "2026-05"
                monthly_counts[month_key] += 1
        monthly_counts = dict(sorted(monthly_counts.items()))

    except Exception as e:
        total_patients = total_preds = flagged_count = 0
        recent_preds   = []
        risk_dist      = {"low": 0, "medium": 0, "high": 0}
        disease_counts = {}
        monthly_counts = {}

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
        "monthly_counts": monthly_counts,
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