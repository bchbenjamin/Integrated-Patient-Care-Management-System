"""
calendar_schedule.py — Medication schedule expansion for FullCalendar.
Computes recurring medication reminder events from prescription data
without materializing individual dose rows.
"""
import json
import datetime
from fastapi import APIRouter, Request, HTTPException
from app.core.db import fetch_all, fetch_one

router = APIRouter()


def expand_prescription_events(prescription: dict, range_start: datetime.date, range_end: datetime.date) -> list[dict]:
    """Expand a single prescription into calendar event dicts within the given date range.
    
    Uses dose_times (fixed daily times) or interval_hours (every N hours) 
    to compute occurrences. Returns FullCalendar-compatible event dicts.
    """
    events = []
    
    p_start = prescription.get('start_date')
    p_end = prescription.get('end_date')
    
    if not p_start or not p_end:
        return events
    
    # Clamp to requested range
    if isinstance(p_start, str):
        p_start = datetime.date.fromisoformat(p_start)
    if isinstance(p_end, str):
        p_end = datetime.date.fromisoformat(p_end)
    
    eff_start = max(p_start, range_start)
    eff_end = min(p_end, range_end)
    
    if eff_start > eff_end:
        return events
    
    medicine = prescription.get('medicine_name', 'Medication')
    dosage = prescription.get('dosage', '')
    rx_id = prescription.get('id')
    
    title = f"Rx: {medicine}"
    if dosage:
        title += f" ({dosage})"
    
    dose_times_raw = prescription.get('dose_times')
    interval_hours = prescription.get('interval_hours')
    
    # Parse dose_times from JSON if it's a string
    dose_times = None
    if dose_times_raw:
        if isinstance(dose_times_raw, str):
            try:
                dose_times = json.loads(dose_times_raw)
            except (json.JSONDecodeError, TypeError):
                dose_times = None
        elif isinstance(dose_times_raw, list):
            dose_times = dose_times_raw
    
    if dose_times:
        # Fixed daily times expansion
        current = eff_start
        while current <= eff_end:
            for t_str in dose_times:
                try:
                    parts = t_str.strip().split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    dt = datetime.datetime.combine(current, datetime.time(hour, minute))
                    events.append({
                        'title': title,
                        'start': dt.isoformat(),
                        'end': (dt + datetime.timedelta(minutes=30)).isoformat(),
                        'backgroundColor': '#b6ced5',
                        'borderColor': '#8fb3bf',
                        'textColor': '#0f3e17',
                        'extendedProps': {
                            'type': 'medication',
                            'prescription_id': rx_id,
                        },
                    })
                except (ValueError, IndexError):
                    continue
            current += datetime.timedelta(days=1)
    
    elif interval_hours and interval_hours > 0:
        # Every-N-hours expansion
        created_at = prescription.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                start_dt = datetime.datetime.fromisoformat(created_at)
            elif isinstance(created_at, datetime.datetime):
                start_dt = created_at
            else:
                start_dt = datetime.datetime.combine(eff_start, datetime.time(8, 0))
        else:
            start_dt = datetime.datetime.combine(eff_start, datetime.time(8, 0))
        
        # Clamp start to range
        range_start_dt = datetime.datetime.combine(eff_start, datetime.time(0, 0))
        range_end_dt = datetime.datetime.combine(eff_end, datetime.time(23, 59))
        
        current_dt = start_dt
        # Fast-forward to range start if needed
        if current_dt < range_start_dt:
            intervals_to_skip = int((range_start_dt - current_dt).total_seconds() // (interval_hours * 3600))
            current_dt += datetime.timedelta(hours=interval_hours * intervals_to_skip)
        
        while current_dt <= range_end_dt:
            if current_dt >= range_start_dt:
                events.append({
                    'title': title,
                    'start': current_dt.isoformat(),
                    'end': (current_dt + datetime.timedelta(minutes=30)).isoformat(),
                    'backgroundColor': '#b6ced5',
                    'borderColor': '#8fb3bf',
                    'textColor': '#0f3e17',
                    'extendedProps': {
                        'type': 'medication',
                        'prescription_id': rx_id,
                    },
                })
            current_dt += datetime.timedelta(hours=interval_hours)
    
    else:
        # Fallback: no structured schedule, show one daily event
        current = eff_start
        while current <= eff_end:
            dt = datetime.datetime.combine(current, datetime.time(9, 0))
            events.append({
                'title': title,
                'start': dt.isoformat(),
                'end': (dt + datetime.timedelta(minutes=30)).isoformat(),
                'backgroundColor': '#b6ced5',
                'borderColor': '#8fb3bf',
                'textColor': '#0f3e17',
                'extendedProps': {
                    'type': 'medication',
                    'prescription_id': rx_id,
                },
            })
            current += datetime.timedelta(days=1)
    
    return events


@router.get("/api/calendar/medications")
async def get_medication_events(request: Request, start: str = "", end: str = ""):
    """Return medication reminder events for FullCalendar within a date range."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Parse date range
    try:
        if start:
            range_start = datetime.date.fromisoformat(start[:10])
        else:
            range_start = datetime.date.today() - datetime.timedelta(days=30)
        
        if end:
            range_end = datetime.date.fromisoformat(end[:10])
        else:
            range_end = datetime.date.today() + datetime.timedelta(days=60)
    except ValueError:
        range_start = datetime.date.today() - datetime.timedelta(days=30)
        range_end = datetime.date.today() + datetime.timedelta(days=60)
    
    # Fetch prescriptions for the current user
    if user['role'] == 'patient':
        patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (user['id'],))
        if not patient:
            return []
        prescriptions = fetch_all(
            "SELECT * FROM prescriptions WHERE patient_id = %s AND start_date IS NOT NULL AND end_date IS NOT NULL",
            (patient['id'],)
        )
    elif user['role'] == 'doctor':
        doctor = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
        if not doctor:
            return []
        prescriptions = fetch_all(
            "SELECT * FROM prescriptions WHERE doctor_id = %s AND start_date IS NOT NULL AND end_date IS NOT NULL",
            (doctor['id'],)
        )
    else:
        return []
    
    # Expand all prescriptions into events
    all_events = []
    for rx in prescriptions:
        all_events.extend(expand_prescription_events(rx, range_start, range_end))
    
    return all_events
