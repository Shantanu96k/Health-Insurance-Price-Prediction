# main.py
"""
MedPredict — FastAPI Entry Point
=================================
Run with:
    uvicorn main:app --reload

Auto-generated API docs:
    http://localhost:8000/docs      ← Use this in your viva demo!
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routes import auth, patient, insurance

# ── Create app ────────────────────────────────────────────────────────
app = FastAPI(
    title="MedPredict",
    description="AI-powered medical history prediction and insurance recommendation system.",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI — show in viva
    redoc_url="/redoc",
)

# ── Session middleware (required for request.session) ─────────────────
# SECRET_KEY is read from .env file via settings
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# ── Static files (CSS, JS) ────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Jinja2 templates ──────────────────────────────────────────────────
templates = Jinja2Templates(directory="app/templates")

# ── Register route modules ────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(patient.router,   prefix="/patient",   tags=["Patient"])
app.include_router(insurance.router, prefix="/insurance", tags=["Insurance"])


# ── Root redirect ─────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root(request: Request):
    """
    If logged in → go to dashboard.
    If not       → go to login.
    """
    if request.session.get("patient_id"):
        return RedirectResponse("/patient/dashboard", status_code=302)
    return RedirectResponse("/auth/login", status_code=302)


# ── Health check (useful for deployment) ──────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Simple ping endpoint to check if the server is running."""
    return {"status": "ok", "app": "MedPredict", "version": "1.0.0"}
