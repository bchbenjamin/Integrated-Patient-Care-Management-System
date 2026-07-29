from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.core.db import fetch_one, fetch_all, execute_query
from app.services.prescription_pdf import generate_prescription_pdf
import datetime
import json
import io

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.get("/prescribe", response_class=HTMLResponse)
async def get_prescribe(request: Request):
    user = get_current_user(request)
    if user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can prescribe")
    
    doctor = fetch_one("SELECT * FROM doctors WHERE user_id = %s", (user["id"],))
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
        
    patients = fetch_all("""
        SELECT DISTINCT p.id, u.full_name 
        FROM patients p
        JOIN users u ON p.user_id = u.id
        JOIN appointments a ON a.patient_id = p.id
        WHERE a.doctor_id = %s
    """, (doctor["id"],))
    
    return templates.TemplateResponse(request=request, name="prescribe.html", context={
        "request": request,
        "user": user,
        "doctor": doctor,
        "patients": patients
    })

@router.post("/prescribe")
async def post_prescribe(
    request: Request,
    patient_id: int = Form(...),
    medicine_name: str = Form(...),
    dosage: str = Form(...),
    schedule_type: str = Form(...),
    frequency: str = Form(...),
    duration_days: int = Form(...),
    notes: str = Form(""),
    dose_times: str = Form(""),
    interval_hours: int = Form(None)
):
    user = get_current_user(request)
    if user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can prescribe")
    
    doctor = fetch_one("SELECT * FROM doctors WHERE user_id = %s", (user["id"],))
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=duration_days)
    
    dose_times_json = None
    final_interval = None
    if schedule_type == 'fixed_times':
        times_list = [t.strip() for t in dose_times.split(',') if t.strip()]
        dose_times_json = json.dumps(times_list)
    elif schedule_type == 'interval':
        final_interval = interval_hours
    
    execute_query("""
        INSERT INTO prescriptions 
        (patient_id, doctor_id, medicine_name, dosage, frequency, duration_days, created_at, dose_times, interval_hours, start_date, end_date, notes)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
    """, (patient_id, doctor["id"], medicine_name, dosage, frequency, duration_days, dose_times_json, final_interval, start_date, end_date, notes))
    
    return RedirectResponse(url="/doctor_dashboard", status_code=303)

@router.get("/prescriptions/{id}/download")
async def download_prescription(request: Request, id: int):
    user = get_current_user(request)
    
    prescription = fetch_one("SELECT * FROM prescriptions WHERE id = %s", (id,))
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
        
    patient = fetch_one("""
        SELECT p.*, u.full_name, p.date_of_birth, p.gender, p.blood_group
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = %s
    """, (prescription["patient_id"],))
    
    doctor = fetch_one("""
        SELECT d.*, u.full_name, s.name as specialty, d.qualification
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        JOIN specialties s ON d.specialty_id = s.id
        WHERE d.id = %s
    """, (prescription["doctor_id"],))
    
    if user["role"] == "patient":
        patient_record = fetch_one("SELECT id FROM patients WHERE user_id = %s", (user["id"],))
        if not patient_record or patient_record["id"] != prescription["patient_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif user["role"] == "doctor":
        doctor_record = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user["id"],))
        if not doctor_record or doctor_record["id"] != prescription["doctor_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    medicines = [{
        "medicine_name": prescription["medicine_name"],
        "dosage": prescription["dosage"],
        "frequency": prescription["frequency"],
        "duration_days": prescription["duration_days"],
        "start_date": prescription["start_date"],
        "end_date": prescription["end_date"],
        "dose_times": json.loads(prescription["dose_times"]) if prescription["dose_times"] else None,
        "interval_hours": prescription["interval_hours"]
    }]
    
    pdf_bytes = generate_prescription_pdf(patient, doctor, medicines, prescription["notes"])
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=prescription_{id}.pdf"}
    )
