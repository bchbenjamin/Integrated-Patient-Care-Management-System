from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.auth import login_user, register_patient
import os
import httpx
from urllib.parse import urlencode

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/")
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = login_user(email, password)
    if user:
        # Convert date/datetime to string for JSON serialization in session
        for k, v in user.items():
            if hasattr(v, "isoformat"):
                user[k] = v.isoformat()
        request.session["user"] = user
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid email or password"})

@router.post("/register")
async def register(
    request: Request, 
    full_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...),
    phone: str = Form(None),
    gender: str = Form("Other"),
    blood_group: str = Form("O+"),
    date_of_birth: str = Form(None),
    emergency_contact: str = Form(None)
):
    success, msg = register_patient(email, password, full_name, phone, date_of_birth, gender, blood_group, emergency_contact)
    if success:
        user = login_user(email, password)
        if user:
            for k, v in user.items():
                if hasattr(v, "isoformat"):
                    user[k] = v.isoformat()
            request.session["user"] = user
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "reg_error": msg})

@router.get("/auth/google/patient-login")
async def google_patient_login(request: Request):
    """Initiate Google OAuth2 login for patients.
    Combines profile, calendar, and health scopes so patients
    auto-connect their integrations on first login."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return RedirectResponse("/login")
    
    # Combine all scopes: profile + calendar + health
    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
        "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
        "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
    ]
    
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": "patient_login",
    }
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")
