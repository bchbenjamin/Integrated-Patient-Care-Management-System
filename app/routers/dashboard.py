from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.db import fetch_one, fetch_all, execute_query

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/patient_dashboard", response_class=HTMLResponse)
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
    
    prescriptions = fetch_all("""
        SELECT p.*, u.full_name as doctor_name,
               (SELECT COUNT(*) FROM medication_logs l WHERE l.prescription_id = p.id AND l.date_taken = CURDATE()) as taken_today
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE p.patient_id = %s
    """, (patient['id'],))
    
    import json
    def date_handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
            
    json_appointments = json.dumps(appointments, default=date_handler)
    
    return templates.TemplateResponse(request=request, name="patient_dashboard.html", context={
        "request": request, 
        "user": user,
        "patient": patient,
        "appointments": appointments,
        "json_appointments": json_appointments,
        "prescriptions": prescriptions
    })

@router.get("/doctor_dashboard", response_class=HTMLResponse)
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
    
    prescriptions = fetch_all("""
        SELECT p.*, u.full_name as patient_name
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.id
        JOIN users u ON pt.user_id = u.id
        WHERE p.doctor_id = %s
    """, (doctor['id'],))
    
    # Also fetch all patients for the doctor to prescribe to
    my_patients = fetch_all("""
        SELECT DISTINCT p.id, u.full_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = %s
    """, (doctor['id'],))
    
    import json
    def date_handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
            
    json_appointments = json.dumps(appointments, default=date_handler)
    
    return templates.TemplateResponse(request=request, name="doctor_dashboard.html", context={
        "request": request, 
        "user": user,
        "doctor": doctor,
        "appointments": appointments,
        "json_appointments": json_appointments,
        "prescriptions": prescriptions,
        "my_patients": my_patients
    })

@router.get("/admin_dashboard", response_class=HTMLResponse)
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

@router.post("/update_availability")
async def update_availability(request: Request, availability: str = Form(...)):
    user = request.session.get("user")
    if user and user['role'] == 'doctor':
        execute_query("UPDATE doctors SET availability = %s WHERE user_id = %s", (availability, user['id']))
    return RedirectResponse("/doctor_dashboard", status_code=303)

@router.post("/update_appointment")
async def update_appointment(request: Request, id: int = Form(...), status: str = Form(...)):
    user = request.session.get("user")
    if user and user['role'] == 'doctor':
        # Ensure the appointment actually belongs to this doctor
        doctor = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
        if doctor:
            execute_query("UPDATE appointments SET status = %s WHERE id = %s AND doctor_id = %s", (status, id, doctor['id']))
    return RedirectResponse("/doctor_dashboard", status_code=303)

@router.get("/book", response_class=HTMLResponse)
async def book_page(request: Request):
    user = request.session.get("user")
    if not user or user['role'] != 'patient':
        return RedirectResponse("/login")
    specialties = fetch_all("SELECT * FROM specialties")
    doctors = fetch_all("SELECT d.id, u.full_name, s.name as specialty FROM doctors d JOIN users u ON d.user_id = u.id JOIN specialties s ON d.specialty_id = s.id")
    return templates.TemplateResponse(request=request, name="book.html", context={"request": request, "user": user, "specialties": specialties, "doctors": doctors})

@router.post("/book")
async def process_booking(request: Request, doctor_id: int = Form(...), date: str = Form(...), time: str = Form(...), reason: str = Form(...)):
    user = request.session.get("user")
    if not user or user['role'] != 'patient':
        return RedirectResponse("/login")
    patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (user['id'],))
    execute_query(
        "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, reason) VALUES (%s, %s, %s, %s, 'scheduled', %s)",
        (patient['id'], doctor_id, date, time, reason)
    )
    return RedirectResponse("/patient_dashboard", status_code=303)

@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    import json
    def date_handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)

    appointments = []
    doctors = []
    
    if user['role'] == 'patient':
        patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (user['id'],))
        if patient:
            appointments = fetch_all("""
                SELECT a.*, u.full_name as doctor_name 
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                JOIN users u ON d.user_id = u.id
                WHERE a.patient_id = %s
            """, (patient['id'],))
        doctors = fetch_all("SELECT d.id, u.full_name, s.name as specialty FROM doctors d JOIN users u ON d.user_id = u.id JOIN specialties s ON d.specialty_id = s.id")
    elif user['role'] == 'doctor':
        doctor = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
        if doctor:
            appointments = fetch_all("""
                SELECT a.*, u.full_name as patient_name 
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN users u ON p.user_id = u.id
                WHERE a.doctor_id = %s
            """, (doctor['id'],))

    json_appointments = json.dumps(appointments, default=date_handler)
    
    return templates.TemplateResponse(request=request, name="calendar_standalone.html", context={
        "request": request, 
        "user": user,
        "json_appointments": json_appointments,
        "doctors": doctors
    })

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request=request, name="settings.html", context={"request": request, "user": user})

@router.post("/settings")
async def update_settings(request: Request, full_name: str = Form(...), phone: str = Form(None)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    execute_query("UPDATE users SET full_name = %s, phone = %s WHERE id = %s", (full_name, phone, user['id']))
    user['full_name'] = full_name
    user['phone'] = phone
    request.session["user"] = user
    return RedirectResponse(f"/{user['role']}_dashboard", status_code=303)

import httpx
from app.services.medicine_lookup import search_medicines_rxnorm

@router.get("/api/medicines/search")
async def search_medicines_api(q: str = ""):
    if not q or len(q) < 2:
        return []
    return await search_medicines_rxnorm(q)

@router.get("/api/medicines/detail")
async def medicine_detail_api(name: str = ""):
    if not name or len(name) < 2:
        return []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{name}*&limit=10")
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("results", []):
                    brand = item.get("openfda", {}).get("brand_name")
                    if brand and brand[0] not in results:
                        results.append(brand[0])
                return results
    except Exception:
        pass
    return []

@router.post("/api/prescribe")
async def prescribe_medication(
    request: Request,
    patient_id: int = Form(...),
    medicine_name: str = Form(...),
    dosage: str = Form(...),
    frequency: str = Form(...),
    duration_days: int = Form(...)
):
    user = request.session.get("user")
    if not user or user['role'] != 'doctor':
        return RedirectResponse("/login")
        
    doctor = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
    execute_query(
        "INSERT INTO prescriptions (patient_id, doctor_id, medicine_name, dosage, frequency, duration_days) VALUES (%s, %s, %s, %s, %s, %s)",
        (patient_id, doctor['id'], medicine_name, dosage, frequency, duration_days)
    )
    return RedirectResponse("/doctor_dashboard", status_code=303)

@router.post("/api/medication/log")
async def log_medication(request: Request, prescription_id: int = Form(...)):
    user = request.session.get("user")
    if not user or user['role'] != 'patient':
        return RedirectResponse("/login")
        
    import datetime
    now = datetime.datetime.now()
    try:
        execute_query(
            "INSERT INTO medication_logs (prescription_id, date_taken, time_taken) VALUES (%s, %s, %s)",
            (prescription_id, now.date(), now.time())
        )
    except Exception:
        pass # Probably duplicate for today
    return RedirectResponse("/patient_dashboard", status_code=303)
