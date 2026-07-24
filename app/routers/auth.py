from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.auth import login_user, register_patient

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

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")
