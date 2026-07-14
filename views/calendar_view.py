from icons import get_svg_icon
"""
calendar_view.py — Monthly Calendar View
Shows appointments as color-coded events. Patients can click dates to book.
"""

import streamlit as st
from streamlit_calendar import calendar
from db import fetch_all, fetch_one
from datetime import datetime


def render(user):
    st.markdown("<div class='eyebrow'>CALENDAR</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Monthly Schedule</h2>", unsafe_allow_html=True)

    role = user['role']

    # Fetch events based on role
    if role == 'admin':
        events_data = fetch_all("""
            SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.reason,
                   up.full_name as patient_name, ud.full_name as doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users up ON p.user_id = up.id
            JOIN doctors d ON a.doctor_id = d.id
            JOIN users ud ON d.user_id = ud.id
            ORDER BY a.appointment_date
        """)
    elif role == 'doctor':
        doctor = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
        if not doctor:
            st.error("Doctor profile not found.")
            return
        events_data = fetch_all("""
            SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.reason,
                   up.full_name as patient_name, '' as doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users up ON p.user_id = up.id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date
        """, (doctor['id'],))
    else:  # patient
        patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (user['id'],))
        if not patient:
            st.error("Patient profile not found.")
            return
        events_data = fetch_all("""
            SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.reason,
                   '' as patient_name, ud.full_name as doctor_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN users ud ON d.user_id = ud.id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date
        """, (patient['id'],))

    # Convert to calendar events
    status_colors = {
        'scheduled': '#0f3e17',
        'completed': '#b1dbb8',
        'cancelled': '#b6ced5',
    }

    events = []
    for evt in events_data:
        date_str = str(evt['appointment_date'])
        time_str = str(evt['appointment_time'])[:5] if evt['appointment_time'] else '00:00'

        # Build title
        if role == 'admin':
            title = f"{evt['patient_name']} → {evt['doctor_name']}"
        elif role == 'doctor':
            title = f"{evt['patient_name']} — {evt['reason'] or 'Appointment'}"
        else:
            title = f"{evt['doctor_name']} — {evt['reason'] or 'Appointment'}"

        events.append({
            "title": title,
            "start": f"{date_str}T{time_str}:00",
            "end": f"{date_str}T{time_str}:00",
            "backgroundColor": status_colors.get(evt['status'], '#222222'),
            "borderColor": status_colors.get(evt['status'], '#222222'),
        })

    # Calendar options
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        },
        "editable": False,
        "selectable": True,
        "navLinks": True,
        "height": 650,
        "dateClick": True,
    }

    custom_css = """
        .fc-toolbar-title {
            font-family: 'Cormorant Garamond', serif !important;
            font-weight: 300 !important;
            color: #0f3e17 !important;
        }
        .fc-button-primary {
            background-color: #0f3e17 !important;
            border-color: #0f3e17 !important;
        }
        .fc-button-primary:hover {
            background-color: #0c2f10 !important;
        }
        .fc-daygrid-day:hover {
            background-color: #e1f4df !important;
        }
        .fc-event {
            border-radius: 7px !important;
            font-size: 11px !important;
        }
    """

    with st.spinner("Loading calendar data..."):
        result = calendar(events=events, options=calendar_options, custom_css=custom_css, key="main_calendar")

    if result and result.get("callback") == "dateClick" and role == 'patient':
        clicked_date = result.get("dateClick", {}).get("dateStr")
        if clicked_date:
            _book_appointment_modal(patient, clicked_date)

    # Legend
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<span style='display:inline-block; width:12px; height:12px; background:#0f3e17; border-radius:50%; margin-right:7px;'></span> Scheduled", unsafe_allow_html=True)
    with col2:
        st.markdown("<span style='display:inline-block; width:12px; height:12px; background:#b1dbb8; border-radius:50%; margin-right:7px;'></span> Completed", unsafe_allow_html=True)
    with col3:
        st.markdown("<span style='display:inline-block; width:12px; height:12px; background:#b6ced5; border-radius:50%; margin-right:7px;'></span> Cancelled", unsafe_allow_html=True)

@st.dialog("Book Appointment")
def _book_appointment_modal(patient, default_date):
    st.write(f"Booking for **{default_date}**")
    specialties = fetch_all("SELECT id, name FROM specialties ORDER BY name")
    spec_options = {s['name']: s['id'] for s in specialties}
    selected_spec = st.selectbox("Select Specialty", list(spec_options.keys()))
    spec_id = spec_options[selected_spec]
    
    doctors = fetch_all("""
        SELECT d.id, u.full_name, d.qualification, d.availability
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.specialty_id = %s
        ORDER BY u.full_name
    """, (spec_id,))
    
    if not doctors:
        st.warning("No doctors available in this specialty.")
        return
        
    doc_options = {f"{d['full_name']} — {d['qualification'] or ''} ({d['availability']})": d['id'] for d in doctors}
    selected_doc = st.selectbox("Select Doctor", list(doc_options.keys()))
    doc_id = doc_options[selected_doc]
    
    time_val = st.time_input("Time")
    reason = st.text_input("Reason for Visit")
    
    if st.button("Confirm Booking", width='stretch'):
        from db import execute_query
        execute_query("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
            VALUES (%s, %s, %s, %s, %s, 'scheduled')
        """, (patient['id'], doc_id, default_date, time_val.strftime("%H:%M"), reason))
        st.success("Appointment booked successfully!")
        st.rerun()
