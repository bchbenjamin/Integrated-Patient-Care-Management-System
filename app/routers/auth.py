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

import random
from app.services.email_service import send_email

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = login_user(email, password)
    if user:
        for k, v in user.items():
            if hasattr(v, "isoformat"):
                user[k] = v.isoformat()
        
        # 2FA Setup
        code = str(random.randint(100000, 999999))
        request.session["pending_2fa_user"] = user
        request.session["2fa_code"] = code
        
        html_body = f"""
        <h2>Your Ease Health Verification Code</h2>
        <p>Your 2-step verification code is: <strong style="font-size:24px;">{code}</strong></p>
        <p>If you did not request this, please secure your account.</p>
        """
        send_email(user["email"], "Ease Health 2-Step Verification", html_body)
        
        return RedirectResponse("/2fa", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid email or password"})

@router.get("/2fa", response_class=HTMLResponse)
async def two_fa_page(request: Request):
    user = request.session.get("pending_2fa_user")
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request=request, name="2fa.html", context={"request": request, "email": user["email"]})

@router.post("/2fa/verify")
async def verify_2fa(request: Request, code: str = Form(...)):
    expected_code = request.session.get("2fa_code")
    user = request.session.get("pending_2fa_user")
    
    if not user or not expected_code:
        return RedirectResponse("/login")
        
    if code.strip() == expected_code:
        request.session.pop("pending_2fa_user", None)
        request.session.pop("2fa_code", None)
        request.session["user"] = user
        return RedirectResponse("/", status_code=303)
        
    return templates.TemplateResponse(request=request, name="2fa.html", context={"request": request, "email": user["email"], "error": "Invalid code."})

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
        html_body = f"""
        <h2>Welcome to Ease Health!</h2>
        <p>Dear {full_name},</p>
        <p>Your Patient Care Management System for Healthcare Services account has been successfully created.</p>
        <p><strong>Your Details:</strong><br>
        Email: {email}<br>
        DOB: {date_of_birth}<br>
        Blood Group: {blood_group}<br>
        Emergency Contact: {emergency_contact}</p>
        <p>Thank you for choosing Ease Health.</p>
        """
        send_email(email, "Welcome to Ease Health - Your Details", html_body)
        
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
