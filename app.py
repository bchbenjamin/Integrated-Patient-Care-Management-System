from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import uvicorn
from auth import login_user, register_patient
from db import fetch_one, fetch_all, execute_query

app = FastAPI(title="Ease Health IPCMS")

app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Middleware removed. Auth checks are done in endpoints.

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return RedirectResponse(f"/{user['role']}_dashboard")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/")
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = login_user(email, password)
    if user:
        request.session["user"] = user
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid email or password"})

@app.post("/register")
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
        request.session["user"] = user
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "reg_error": msg})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

@app.get("/patient_dashboard", response_class=HTMLResponse)
async def patient_dashboard_page(request: Request):
    user = request.session.get("user")
    if not user or user['role'] != 'patient':
        return RedirectResponse("/login")
    
    patient = fetch_one("SELECT * FROM patients WHERE user_id = %s", (user['id'],))
    appointments = fetch_all("""
        SELECT a.*, d.qualification, u.full_name as doctor_name, s.name as specialty
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN specialties s ON d.specialty_id = s.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date, a.appointment_time
    """, (patient['id'],))
    
    return templates.TemplateResponse(request=request, name="patient_dashboard.html", context={
        "request": request, 
        "user": user,
        "patient": patient,
        "appointments": appointments
    })

@app.get("/doctor_dashboard", response_class=HTMLResponse)
async def doctor_dashboard_page(request: Request):
    user = request.session.get("user")
    if not user or user['role'] != 'doctor':
        return RedirectResponse("/login")
    
    doctor = fetch_one("SELECT d.*, s.name as specialty FROM doctors d JOIN specialties s ON d.specialty_id = s.id WHERE user_id = %s", (user['id'],))
    appointments = fetch_all("""
        SELECT a.*, p.date_of_birth, p.gender, p.blood_group, p.health_condition, u.full_name as patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = %s
        ORDER BY a.appointment_date, a.appointment_time
    """, (doctor['id'],))
    
    return templates.TemplateResponse(request=request, name="doctor_dashboard.html", context={
        "request": request, 
        "user": user,
        "doctor": doctor,
        "appointments": appointments
    })

@app.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    user = request.session.get("user")
    if not user or user['role'] != 'admin':
        return RedirectResponse("/login")
    
    stats = {
        "patients": fetch_one("SELECT COUNT(*) as c FROM patients")['c'],
        "doctors": fetch_one("SELECT COUNT(*) as c FROM doctors")['c'],
        "appointments": fetch_one("SELECT COUNT(*) as c FROM appointments")['c']
    }
    
    return templates.TemplateResponse(request=request, name="admin_dashboard.html", context={
        "request": request, 
        "user": user,
        "stats": stats
    })

@app.post("/update_availability")
async def update_availability(request: Request, availability: str = Form(...)):
    user = request.session.get("user")
    if user and user['role'] == 'doctor':
        execute_query("UPDATE doctors SET availability = %s WHERE user_id = %s", (availability, user['id']))
    return RedirectResponse("/doctor_dashboard", status_code=303)

@app.post("/update_appointment")
async def update_appointment(request: Request, id: int = Form(...), status: str = Form(...)):
    user = request.session.get("user")
    if user and user['role'] == 'doctor':
        execute_query("UPDATE appointments SET status = %s WHERE id = %s", (status, id))
    return RedirectResponse("/doctor_dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
