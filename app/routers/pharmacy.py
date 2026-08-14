"""Pharmacy router — displays available medicines for patients.

Shows two categories:
1. OTC medicines: available to everyone without prescription
2. Prescription medicines: only those matching the patient's active prescriptions
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.db import fetch_all, fetch_one

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/pharmacy", response_class=HTMLResponse)
async def pharmacy_page(request: Request):
    """Display the pharmacy page with OTC and prescribed medicines."""
    user = request.session.get("user")
    if not user or user['role'] != 'patient':
        return RedirectResponse("/login")
    
    # Fetch all OTC medicines in stock
    otc_medicines = fetch_all(
        "SELECT * FROM pharmacy_stock WHERE category = 'otc' AND quantity > 0 ORDER BY medicine_name"
    )
    
    # Fetch prescription medicines matching this patient's active prescriptions
    patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (user['id'],))
    prescribed_medicines = []
    if patient:
        prescribed_medicines = fetch_all("""
            SELECT ps.*, p.dosage as prescribed_dosage, p.frequency as prescribed_frequency,
                   p.duration_days, u.full_name as doctor_name
            FROM pharmacy_stock ps
            INNER JOIN prescriptions p ON LOWER(ps.medicine_name) = LOWER(p.medicine_name)
            INNER JOIN doctors d ON p.doctor_id = d.id
            INNER JOIN users u ON d.user_id = u.id
            WHERE p.patient_id = %s AND ps.quantity > 0
        """, (patient['id'],))
    
    return templates.TemplateResponse(request=request, name="pharmacy.html", context={
        "request": request,
        "user": user,
        "otc_medicines": otc_medicines,
        "prescribed_medicines": prescribed_medicines,
    })
