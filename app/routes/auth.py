# app/routes/auth.py
"""
Authentication routes — Register, Login, Logout.

Flow:
  Register → hash password → store in Supabase patient table → redirect to login
  Login    → fetch patient by email → verify password → create JWT → store in session
  Logout   → clear session → redirect to login
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid

from app.database import supabase
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Passlib context — bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return bcrypt hash of a plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT token.
    Expires after ACCESS_TOKEN_EXPIRE_MINUTES (set in .env).
    """
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def add_flash(request: Request, category: str, message: str):
    """
    Store a one-time flash message in the session.
    base.html reads and displays these messages.
    """
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


# ── GET /auth/login ───────────────────────────────────────────────────

@router.get("/login")
async def login_page(request: Request):
    """Render the login page."""
    # If already logged in, go straight to dashboard
    if request.session.get("patient_id"):
        return RedirectResponse("/patient/dashboard", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "messages": messages}
    )


# ── POST /auth/login ──────────────────────────────────────────────────

@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Process login form.
    1. Look up patient by email in Supabase.
    2. Verify password with bcrypt.
    3. On success → create JWT → save to session → redirect to dashboard.
    4. On failure → flash error → back to login.
    """
    # 1. Fetch patient record
    try:
        result = supabase.table("patient") \
            .select("id, full_name, email, password_hash") \
            .eq("email", email.strip().lower()) \
            .single() \
            .execute()
        patient = result.data
    except Exception:
        patient = None

    # 2. Validate credentials
    if not patient or not verify_password(password, patient["password_hash"]):
        add_flash(request, "error", "Invalid email or password. Please try again.")
        return RedirectResponse("/auth/login", status_code=302)

    # 3. Create JWT and store session info
    token = create_access_token({"sub": patient["id"], "email": patient["email"]})
    request.session["patient_id"]   = patient["id"]
    request.session["patient_name"] = patient["full_name"]
    request.session["token"]        = token

    add_flash(request, "success", f"Welcome back, {patient['full_name']}!")
    return RedirectResponse("/patient/dashboard", status_code=302)


# ── GET /auth/register ────────────────────────────────────────────────

@router.get("/register")
async def register_page(request: Request):
    """Render the registration page."""
    if request.session.get("patient_id"):
        return RedirectResponse("/patient/dashboard", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "messages": messages}
    )


# ── POST /auth/register ───────────────────────────────────────────────

@router.post("/register")
async def register_submit(
    request: Request,
    full_name:        str = Form(...),
    age:              int = Form(...),
    gender:           str = Form(...),
    email:            str = Form(...),
    password:         str = Form(...),
    confirm_password: str = Form(...)
):
    """
    Process registration form.
    1. Validate passwords match.
    2. Check email is not already registered.
    3. Hash password.
    4. Insert new patient into Supabase.
    5. Redirect to login with success message.
    """
    email = email.strip().lower()

    # 1. Password match check
    if password != confirm_password:
        add_flash(request, "error", "Passwords do not match.")
        return RedirectResponse("/auth/register", status_code=302)

    # 2. Minimum password length
    if len(password) < 8:
        add_flash(request, "error", "Password must be at least 8 characters.")
        return RedirectResponse("/auth/register", status_code=302)

    # 3. Check if email already exists
    try:
        existing = supabase.table("patient") \
            .select("id") \
            .eq("email", email) \
            .execute()
        if existing.data:
            add_flash(request, "error", "An account with this email already exists.")
            return RedirectResponse("/auth/register", status_code=302)
    except Exception:
        pass

    # 4. Hash password and insert patient
    hashed = hash_password(password)
    new_id = str(uuid.uuid4())

    try:
        supabase.table("patient").insert({
            "id":            new_id,
            "full_name":     full_name.strip(),
            "age":           age,
            "gender":        gender,
            "email":         email,
            "password_hash": hashed,
        }).execute()
    except Exception as e:
        add_flash(request, "error", f"Registration failed. Please try again. ({str(e)})")
        return RedirectResponse("/auth/register", status_code=302)

    # 5. Success
    add_flash(request, "success", "Account created successfully! Please log in.")
    return RedirectResponse("/auth/login", status_code=302)


# ── GET /auth/logout ──────────────────────────────────────────────────

@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to login."""
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
