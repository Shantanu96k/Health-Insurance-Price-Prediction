import os
import csv
import io
import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

from app.database import supabase

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
pwd_context    = CryptContext(schemes=["bcrypt"], deprecated="auto")

PAGE_SIZE = 20                        



def is_admin(request: Request) -> bool:
    return request.session.get("is_admin", False)


def add_flash(request: Request, cat: str, msg: str):
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((cat, msg))


def guard(request: Request):
    """Return redirect if not admin, else None."""
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=302)
    return None



@router.get("/login")
async def admin_login_page(request: Request):
    if is_admin(request):
        return RedirectResponse("/admin/", status_code=302)
    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_login.html", {"request": request, "messages": messages})


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



@router.get("")
async def admin_redirect():
    return RedirectResponse("/admin/", status_code=307)


@router.get("/")
async def admin_dashboard(request: Request):
    if redir := guard(request):
        return redir

    try:
        all_preds_res = supabase.table("predictions")\
            .select("id, patient_id, predicted_disease, risk_level, confidence_score, honesty_flag, created_at")\
            .order("created_at", desc=True).execute()
        all_preds = all_preds_res.data or []

        total_preds   = len(all_preds)
        recent_preds  = all_preds[:10]
        flagged_count = sum(1 for p in all_preds if p.get("honesty_flag") == "review_needed")

        patients_res  = supabase.table("patient").select("id, created_at").execute()
        all_patients  = patients_res.data or []
        total_patients = len(all_patients)

        risk_dist = {"low": 0, "medium": 0, "high": 0}
        for p in all_preds:
            rl = p.get("risk_level", "low")
            risk_dist[rl] = risk_dist.get(rl, 0) + 1

        disease_counts: dict = defaultdict(int)
        for p in all_preds:
            dis = p.get("predicted_disease") or "Unknown"
            disease_counts[dis] += 1
        disease_counts = dict(disease_counts)

        monthly_counts: dict = defaultdict(int)
        for pt in all_patients:
            if pt.get("created_at"):
                monthly_counts[pt["created_at"][:7]] += 1
        monthly_counts = dict(sorted(monthly_counts.items()))

                                 
        price_res = supabase.table("insurance_price_predictions").select("id").execute()
        total_price_preds = len(price_res.data or [])

    except Exception as e:
        total_patients = total_preds = flagged_count = total_price_preds = 0
        recent_preds   = []
        risk_dist      = {"low": 0, "medium": 0, "high": 0}
        disease_counts = {}
        monthly_counts = {}

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_dashboard.html", {
        "request":          request,
        "messages":         messages,
        "total_patients":   total_patients,
        "total_preds":      total_preds,
        "flagged_count":    flagged_count,
        "total_price_preds": total_price_preds,
        "recent_preds":     recent_preds,
        "risk_dist":        risk_dist,
        "disease_counts":   disease_counts,
        "monthly_counts":   monthly_counts,
    })


@router.get("/patients")
async def admin_patients(request: Request, q: str = ""):
    if redir := guard(request):
        return redir

    try:
        query = supabase.table("patient")\
            .select("id, full_name, email, age, gender, city, blood_group, created_at")\
            .order("created_at", desc=True)
        patients = query.execute().data or []

                                                                                
        if q:
            q_lower = q.lower()
            patients = [p for p in patients if
                        q_lower in (p.get("full_name") or "").lower() or
                        q_lower in (p.get("email") or "").lower() or
                        q_lower in (p.get("city") or "").lower()]
    except Exception:
        patients = []

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_patients.html", {
        "request":  request,
        "patients": patients,
        "messages": messages,
        "q":        q,
    })



@router.get("/patients/add")
async def admin_add_patient_form(request: Request):
    if redir := guard(request):
        return redir
    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_patient_form.html", {
        "request":  request,
        "messages": messages,
        "patient":  {},
        "is_new":   True,
    })


@router.post("/patients/add")
async def admin_add_patient(
    request:   Request,
    full_name: str = Form(...),
    age:       int = Form(...),
    gender:    str = Form(...),
    email:     str = Form(...),
    password:  str = Form(...),
    phone:     str = Form(""),
    city:      str = Form(""),
    blood_group: str = Form(""),
):
    if redir := guard(request):
        return redir

    email = email.strip().lower()

    try:
        existing = supabase.table("patient").select("id").eq("email", email).execute()
        if existing.data:
            add_flash(request, "error", f"Email {email} is already registered.")
            return RedirectResponse("/admin/patients/add", status_code=302)
    except Exception:
        pass

    try:
        supabase.table("patient").insert({
            "id":            str(uuid.uuid4()),
            "full_name":     full_name.strip(),
            "age":           age,
            "gender":        gender,
            "email":         email,
            "password_hash": pwd_context.hash(password),
            "phone":         phone or None,
            "city":          city or None,
            "blood_group":   blood_group or None,
        }).execute()
        add_flash(request, "success", f"Patient '{full_name}' created successfully.")
    except Exception as e:
        add_flash(request, "error", f"Failed to create patient: {e}")
        return RedirectResponse("/admin/patients/add", status_code=302)

    return RedirectResponse("/admin/patients", status_code=302)



@router.get("/patients/{patient_id}")
async def admin_patient_detail(request: Request, patient_id: str):
    if redir := guard(request):
        return redir

    patient = {}
    predictions = []
    insurance   = []
    price_preds = []

    try:
        res = supabase.table("patient").select("*").eq("id", patient_id).single().execute()
        patient = res.data or {}
    except Exception:
        add_flash(request, "error", "Patient not found.")
        return RedirectResponse("/admin/patients", status_code=302)

    try:
        predictions = supabase.table("predictions")\
            .select("id, predicted_disease, risk_level, confidence_score, honesty_flag, created_at")\
            .eq("patient_id", patient_id)\
            .order("created_at", desc=True).execute().data or []
    except Exception:
        pass

    try:
        insurance = supabase.table("insurance_recommendations")\
            .select("id, plan_name, plan_type, monthly_cost, created_at")\
            .eq("patient_id", patient_id)\
            .order("created_at", desc=True).execute().data or []
    except Exception:
        pass

    try:
        price_preds = supabase.table("insurance_price_predictions")\
            .select("id, annual_premium, monthly_premium, premium_band, smoker, age, bmi, created_at")\
            .eq("patient_id", patient_id)\
            .order("created_at", desc=True).execute().data or []
    except Exception:
        pass

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_patient_detail.html", {
        "request":     request,
        "patient":     patient,
        "predictions": predictions,
        "insurance":   insurance,
        "price_preds": price_preds,
        "messages":    messages,
    })



@router.get("/patients/{patient_id}/edit")
async def admin_edit_patient_form(request: Request, patient_id: str):
    if redir := guard(request):
        return redir

    try:
        res = supabase.table("patient").select("*").eq("id", patient_id).single().execute()
        patient = res.data or {}
    except Exception:
        add_flash(request, "error", "Patient not found.")
        return RedirectResponse("/admin/patients", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_patient_form.html", {
        "request":  request,
        "messages": messages,
        "patient":  patient,
        "is_new":   False,
    })


@router.post("/patients/{patient_id}/edit")
async def admin_edit_patient(
    request:    Request,
    patient_id: str,
    full_name:  str = Form(...),
    age:        int = Form(...),
    gender:     str = Form(...),
    email:      str = Form(...),
    phone:      str = Form(""),
    city:       str = Form(""),
    blood_group:      str = Form(""),
    emergency_contact: str = Form(""),
    new_password: str = Form(""),
):
    if redir := guard(request):
        return redir

    update_data = {
        "full_name":          full_name.strip(),
        "age":                age,
        "gender":             gender,
        "email":              email.strip().lower(),
        "phone":              phone or None,
        "city":               city or None,
        "blood_group":        blood_group or None,
        "emergency_contact":  emergency_contact or None,
    }

    if new_password and len(new_password) >= 8:
        update_data["password_hash"] = pwd_context.hash(new_password)
    elif new_password and len(new_password) < 8:
        add_flash(request, "error", "New password must be at least 8 characters.")
        return RedirectResponse(f"/admin/patients/{patient_id}/edit", status_code=302)

    try:
        supabase.table("patient").update(update_data).eq("id", patient_id).execute()
        add_flash(request, "success", "Patient updated successfully.")
    except Exception as e:
        add_flash(request, "error", f"Update failed: {e}")

    return RedirectResponse(f"/admin/patients/{patient_id}", status_code=302)



@router.post("/patients/{patient_id}/delete")
async def admin_delete_patient(request: Request, patient_id: str):
    if redir := guard(request):
        return redir

    try:
                                                            
        supabase.table("patient").delete().eq("id", patient_id).execute()
        add_flash(request, "success", "Patient and all associated data deleted.")
    except Exception as e:
        add_flash(request, "error", f"Delete failed: {e}")

    return RedirectResponse("/admin/patients", status_code=302)


@router.get("/predictions")
async def admin_predictions(request: Request, page: int = 1, risk: str = "", disease: str = ""):
    if redir := guard(request):
        return redir

    offset = (page - 1) * PAGE_SIZE

    try:
        query = supabase.table("predictions")\
            .select("id, patient_id, predicted_disease, risk_level, confidence_score, honesty_flag, mri_consistency, created_at")\
            .order("created_at", desc=True)

        if risk:
            query = query.eq("risk_level", risk)
        if disease:
            query = query.eq("predicted_disease", disease)

        all_preds = query.execute().data or []
        total     = len(all_preds)
        preds     = all_preds[offset: offset + PAGE_SIZE]
        total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

                                             
        diseases = sorted(set(p.get("predicted_disease", "") for p in all_preds if p.get("predicted_disease")))

    except Exception:
        preds = []
        total = 0
        total_pages = 1
        diseases = []

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_predictions.html", {
        "request":     request,
        "predictions": preds,
        "messages":    messages,
        "total":       total,
        "page":        page,
        "total_pages": total_pages,
        "risk_filter": risk,
        "disease_filter": disease,
        "diseases":    diseases,
    })



@router.get("/predictions/{prediction_id}")
async def admin_prediction_detail(request: Request, prediction_id: str):
    if redir := guard(request):
        return redir

    import json

    prediction = {}
    patient    = {}
    try:
        res        = supabase.table("predictions").select("*").eq("id", prediction_id).single().execute()
        prediction = res.data or {}
    except Exception:
        add_flash(request, "error", "Prediction not found.")
        return RedirectResponse("/admin/predictions", status_code=302)

    if prediction.get("patient_id"):
        try:
            res2   = supabase.table("patient").select("full_name, email, age, gender").eq("id", prediction["patient_id"]).single().execute()
            patient = res2.data or {}
        except Exception:
            pass

    form_snap = {}
    ai_tips   = {}
    try:
        form_snap = json.loads(prediction.get("form_snapshot", "{}"))
    except Exception:
        pass
    try:
        ai_tips = json.loads(prediction.get("ai_tips", "{}"))
    except Exception:
        pass

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse("admin_prediction_detail.html", {
        "request":    request,
        "prediction": prediction,
        "patient":    patient,
        "form_snap":  form_snap,
        "ai_tips":    ai_tips,
        "messages":   messages,
    })



@router.post("/predictions/{prediction_id}/delete")
async def admin_delete_prediction(request: Request, prediction_id: str):
    if redir := guard(request):
        return redir

    try:
        supabase.table("predictions").delete().eq("id", prediction_id).execute()
        add_flash(request, "success", "Prediction deleted.")
    except Exception as e:
        add_flash(request, "error", f"Delete failed: {e}")

    return RedirectResponse("/admin/predictions", status_code=302)


@router.get("/flagged")
async def admin_flagged(request: Request):
    if redir := guard(request):
        return redir

    try:
        flagged = supabase.table("predictions")\
            .select("id, patient_id, predicted_disease, risk_level, mri_consistency, honesty_flag, created_at")\
            .eq("honesty_flag", "review_needed")\
            .order("created_at", desc=True).execute().data or []
    except Exception:
        flagged = []

    return templates.TemplateResponse("admin_flagged.html", {
        "request": request,
        "flagged": flagged,
    })



@router.post("/predictions/{prediction_id}/flag")
async def admin_toggle_flag(request: Request, prediction_id: str, action: str = Form(...)):
    """
    Admin can mark a flagged prediction as reviewed / clear the flag.
    action: 'clear' → set honesty_flag = 'trusted'
            'flag'  → set honesty_flag = 'review_needed'
    """
    if redir := guard(request):
        return redir

    new_flag = "trusted" if action == "clear" else "review_needed"
    try:
        supabase.table("predictions").update({"honesty_flag": new_flag}).eq("id", prediction_id).execute()
        add_flash(request, "success", f"Flag updated to '{new_flag}'.")
    except Exception as e:
        add_flash(request, "error", f"Update failed: {e}")

    return RedirectResponse("/admin/flagged", status_code=302)


@router.get("/export")
async def admin_export(request: Request, table: str = "patients"):
    """
    Export a table as a CSV file download.
    table: 'patients' | 'predictions' | 'insurance'
    """
    if redir := guard(request):
        return redir

    output = io.StringIO()
    writer = csv.writer(output)

    try:
        if table == "patients":
            rows = supabase.table("patient")\
                .select("id, full_name, email, age, gender, city, blood_group, phone, created_at")\
                .order("created_at", desc=True).execute().data or []
            if rows:
                writer.writerow(rows[0].keys())
                for r in rows:
                    writer.writerow(r.values())
            filename = "medpredict_patients.csv"

        elif table == "predictions":
            rows = supabase.table("predictions")\
                .select("id, patient_id, predicted_disease, risk_level, confidence_score, honesty_flag, mri_consistency, created_at")\
                .order("created_at", desc=True).execute().data or []
            if rows:
                writer.writerow(rows[0].keys())
                for r in rows:
                    writer.writerow(r.values())
            filename = "medpredict_predictions.csv"

        elif table == "insurance":
            rows = supabase.table("insurance_price_predictions")\
                .select("id, patient_id, age, bmi, smoker, annual_premium, monthly_premium, premium_band, created_at")\
                .order("created_at", desc=True).execute().data or []
            if rows:
                writer.writerow(rows[0].keys())
                for r in rows:
                    writer.writerow(r.values())
            filename = "medpredict_price_predictions.csv"

        else:
            return Response("Invalid table", status_code=400)

    except Exception as e:
        return Response(f"Export failed: {e}", status_code=500)

    return Response(
        content    = output.getvalue(),
        media_type = "text/csv",
        headers    = {"Content-Disposition": f'attachment; filename="{filename}"'},
    )