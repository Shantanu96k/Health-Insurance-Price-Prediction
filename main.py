         
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routes import auth, patient, insurance

from app.routes import insurance_price, admin as admin_routes

app = FastAPI(
    title="MedPredict",
    description=(
        "AI-powered medical history prediction and insurance recommendation system. "
        "Features: Disease prediction (RandomForest), MRI lie detection, "
        "Insurance price prediction (GradientBoosting), Gemini AI suggestions."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(patient.router,   prefix="/patient",   tags=["Patient"])
app.include_router(insurance.router, prefix="/insurance", tags=["Insurance"])

app.include_router(insurance_price.router, prefix="/price", tags=["Insurance Price Prediction"])
app.include_router(admin_routes.router,    prefix="/admin", tags=["Admin"])


@app.get("/", include_in_schema=False)
async def root(request: Request):
    if request.session.get("patient_id"):
        return RedirectResponse("/patient/dashboard", status_code=302)
    return RedirectResponse("/auth/login", status_code=302)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": "MedPredict",
        "version": "2.0.0",
        "features": [
            "disease-prediction",
            "mri-validation",
            "insurance-plans",
            "insurance-price-prediction",
            "gemini-ai-suggestions",
            "admin-dashboard",
        ]
    }