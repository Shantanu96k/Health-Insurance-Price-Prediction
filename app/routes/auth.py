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

                                               
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


                                                                       

def hash_password(plain: str) -> str:
                                                      
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
                                                              
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
       
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def add_flash(request: Request, category: str, message: str):
       
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append((category, message))


                                                                        

@router.get("/login")
async def login_page(request: Request):
                                
                                                    
    if request.session.get("patient_id"):
        return RedirectResponse("/patient/dashboard", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "messages": messages}
    )


                                                                        

@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
       
                             
    try:
        result = supabase.table("patient")\
            .select("id, full_name, email, password_hash")\
            .eq("email", email.strip().lower())\
            .single()\
            .execute()
        patient = result.data
    except Exception:
        patient = None

                             
    if not patient or not verify_password(password, patient["password_hash"]):
        add_flash(request, "error", "Invalid email or password. Please try again.")
        return RedirectResponse("/auth/login", status_code=302)

                                          
    token = create_access_token({"sub": patient["id"], "email": patient["email"]})
    request.session["patient_id"]   = patient["id"]
    request.session["patient_name"] = patient["full_name"]
    request.session["token"]        = token

    add_flash(request, "success", f"Welcome back, {patient['full_name']}!")
    return RedirectResponse("/patient/dashboard", status_code=302)


                                                                        

@router.get("/register")
async def register_page(request: Request):
                                       
    if request.session.get("patient_id"):
        return RedirectResponse("/patient/dashboard", status_code=302)

    messages = request.session.pop("messages", [])
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "messages": messages}
    )


                                                                        

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
       
    email = email.strip().lower()

                             
    if password != confirm_password:
        add_flash(request, "error", "Passwords do not match.")
        return RedirectResponse("/auth/register", status_code=302)

                                
    if len(password) < 8:
        add_flash(request, "error", "Password must be at least 8 characters.")
        return RedirectResponse("/auth/register", status_code=302)

                                      
    try:
        existing = supabase.table("patient")\
            .select("id")\
            .eq("email", email)\
            .execute()
        if existing.data:
            add_flash(request, "error", "An account with this email already exists.")
            return RedirectResponse("/auth/register", status_code=302)
    except Exception:
        pass

                                         
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

                
    add_flash(request, "success", "Account created successfully! Please log in.")
    return RedirectResponse("/auth/login", status_code=302)


                                                                        

@router.get("/logout")
async def logout(request: Request):
                                              
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
