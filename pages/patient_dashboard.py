"""
patient_dashboard.py — Patient Dashboard
Health summary, book appointments, history, AI assistant with profile context.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
import time
import os
import json
from dotenv import load_dotenv
from db import fetch_all, fetch_one, execute_query

EASE_COLORS = ["#0f3e17", "#b1dbb8", "#b6ced5", "#cfe7d3", "#e1f4df", "#0c2f10"]


def render(user):
    patient = fetch_one("SELECT * FROM patients WHERE user_id = %s", (user['id'],))
    if not patient:
        st.error("Patient profile not found.")
        return

    st.markdown("<div class='eyebrow'>PATIENT PORTAL</div>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='margin-top:0;'>Welcome, {user['full_name']}</h1>", unsafe_allow_html=True)

    tab_health, tab_book, tab_history, tab_ai, tab_analytics = st.tabs(
        ["Health Summary", "Book Appointment", "My Appointments", "AI Assistant", "Analytics"]
    )

    with tab_health:
        _render_health(patient, user)

    with tab_book:
        _render_booking(patient)

    with tab_history:
        _render_history(patient)

    with tab_ai:
        _render_ai_assistant(patient, user)

    with tab_analytics:
        _render_analytics(patient)


def _render_health(patient, user):
    st.markdown("<div class='eyebrow'>HEALTH SUMMARY</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Your Profile</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Full Name:** {user['full_name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Phone:** {user.get('phone', 'N/A')}")
        st.write(f"**Date of Birth:** {patient.get('date_of_birth', 'N/A')}")
    with col2:
        st.write(f"**Gender:** {patient.get('gender', 'N/A')}")
        st.write(f"**Blood Group:** {patient.get('blood_group', 'N/A')}")
        st.write(f"**Emergency Contact:** {patient.get('emergency_contact', 'N/A')}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #e1f4df; border-radius: 14px; padding: 28px;">
        <div class="eyebrow">HEALTH CONDITION</div>
        <p style="font-size: 14px; color: #222; margin-top: 7px;">{}</p>
        <p style="font-size: 11px; color: #71717a; margin-top: 14px;">This field can only be updated by your doctor or an administrator.</p>
    </div>
    """.format(patient.get('health_condition') or 'No condition recorded yet.'), unsafe_allow_html=True)


def _render_booking(patient):
    st.markdown("<div class='eyebrow'>BOOK APPOINTMENT</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Schedule a Visit</h2>", unsafe_allow_html=True)

    # Step 1: Select specialty
    specialties = fetch_all("SELECT id, name FROM specialties ORDER BY name")
    spec_options = {s['name']: s['id'] for s in specialties}
    selected_spec = st.selectbox("Select Specialty", list(spec_options.keys()))
    spec_id = spec_options[selected_spec]

    # Step 2: Show available doctors
    doctors = fetch_all("""
        SELECT d.id, u.full_name, d.qualification, d.experience_years, d.availability
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.specialty_id = %s AND d.availability = 'available'
        ORDER BY u.full_name
    """, (spec_id,))

    if not doctors:
        st.warning("No available doctors in this specialty right now.")
        return

    doc_options = {f"{d['full_name']} — {d['qualification'] or ''} ({d['experience_years']}y)": d['id'] for d in doctors}
    selected_doc = st.selectbox("Select Doctor", list(doc_options.keys()))
    doc_id = doc_options[selected_doc]

    # Step 3: Date & Time
    col1, col2 = st.columns(2)
    with col1:
        from datetime import date, timedelta
        appt_date = st.date_input("Appointment Date", min_value=date.today(), value=date.today() + timedelta(days=1))
    with col2:
        appt_time = st.time_input("Appointment Time")

    reason = st.text_area("Reason for Visit")

    if st.button("Book Appointment"):
        if not reason.strip():
            st.error("Please provide a reason for your visit.")
        else:
            # Check for duplicate
            existing = fetch_one(
                "SELECT id FROM appointments WHERE patient_id=%s AND doctor_id=%s AND appointment_date=%s AND appointment_time=%s AND status='scheduled'",
                (patient['id'], doc_id, appt_date.isoformat(), appt_time.strftime('%H:%M:%S'))
            )
            if existing:
                st.warning("You already have an appointment at this time with this doctor.")
            else:
                execute_query(
                    "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason) VALUES (%s, %s, %s, %s, %s)",
                    (patient['id'], doc_id, appt_date.isoformat(), appt_time.strftime('%H:%M:%S'), reason)
                )
                st.success("Appointment booked successfully.")
                st.rerun()


def _render_history(patient):
    st.markdown("<div class='eyebrow'>APPOINTMENT HISTORY</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Your Visits</h2>", unsafe_allow_html=True)

    appts = fetch_all("""
        SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.reason, a.notes,
               u.full_name as doctor_name, s.name as specialty
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (patient['id'],))

    if appts:
        for appt in appts:
            date_str = str(appt['appointment_date'])
            time_str = str(appt['appointment_time'])[:5] if appt['appointment_time'] else ''
            status_color = {'scheduled': '#0f3e17', 'completed': '#b1dbb8', 'cancelled': '#b6ced5'}.get(appt['status'], '#222')

            st.markdown(f"""
            <div style="background-color: #e1f4df; border-radius: 14px; padding: 21px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{appt['doctor_name']}</strong> · {appt['specialty'] or 'General'}<br>
                        <span style="font-size:12px; color:#222;">{date_str} at {time_str}</span>
                    </div>
                    <span style="background-color: {status_color}; color: #fffefc; padding: 4px 12px; border-radius: 999px; font-size: 12px;">{appt['status']}</span>
                </div>
                <p style="font-size:13px; margin-top:7px; color:#222;"><strong>Reason:</strong> {appt['reason'] or 'N/A'}</p>
                {'<p style="font-size:13px; color:#0f3e17;"><strong>Doctor Notes:</strong> ' + appt["notes"] + '</p>' if appt.get("notes") else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No appointments yet. Book your first visit!")


def _render_ai_assistant(patient, user):
    st.markdown("<div class='eyebrow'>AI CLINICAL ASSISTANT</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Intelligent Query</h2>", unsafe_allow_html=True)

    # Build profile context
    upcoming = fetch_all("""
        SELECT a.appointment_date, a.appointment_time, u.full_name as doctor_name, s.name as specialty
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        WHERE a.patient_id = %s AND a.status = 'scheduled' AND a.appointment_date >= CURDATE()
        ORDER BY a.appointment_date
    """, (patient['id'],))

    available_doctors = fetch_all("""
        SELECT u.full_name, s.name as specialty, d.id as doctor_id
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        WHERE d.availability = 'available'
    """)

    upcoming_text = "\n".join([f"- {a['appointment_date']} at {str(a['appointment_time'])[:5]} with {a['doctor_name']} ({a['specialty']})" for a in upcoming]) if upcoming else "No upcoming appointments."
    doctors_text = "\n".join([f"- {d['full_name']} ({d['specialty']})" for d in available_doctors]) if available_doctors else "No doctors available."

    system_prompt = f"""You are a clinical assistant for the Ease Health patient care system.
You are speaking with patient: {user['full_name']}
Health condition: {patient.get('health_condition') or 'None recorded'}
Blood group: {patient.get('blood_group') or 'Unknown'}

Upcoming appointments:
{upcoming_text}

Available doctors for booking:
{doctors_text}

If the patient asks to book an appointment, recommend the most suitable doctor based on their health condition and the specialty of available doctors. Provide helpful medical guidance (but remind them you're an AI, not a replacement for professional advice).

If the user wants to book, respond with a JSON block like:
```json
{{"action": "book", "doctor_name": "...", "reason": "..."}}
```
Otherwise respond naturally."""

    st.markdown(f"<p style='font-size:14px; color:#222; margin-bottom:21px;'>Powered by Groq & Langchain · Profile-aware for <strong>{user['full_name']}</strong></p>", unsafe_allow_html=True)

    user_input = st.text_area(
        "Ask me anything about your health or appointments:",
        value="What appointments do I have coming up?"
    )

    if st.button("Submit Query"):
        if not user_input.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Analyzing..."):
                time.sleep(1)
                load_dotenv()
                api_key = os.getenv("GROQ_API_KEY")

                if api_key:
                    try:
                        from langchain_groq import ChatGroq
                        from langchain_core.messages import HumanMessage, SystemMessage

                        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, api_key=api_key)
                        response = llm.invoke([
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=user_input)
                        ])
                        reply = response.content
                        st.success("Analysis Complete")
                        st.markdown(reply)

                        # Check for auto-book action
                        if '```json' in reply:
                            try:
                                json_str = reply.split('```json')[1].split('```')[0].strip()
                                action_data = json.loads(json_str)
                                if action_data.get('action') == 'book':
                                    doc_name = action_data.get('doctor_name', '')
                                    reason = action_data.get('reason', 'AI-recommended appointment')
                                    # Find doctor
                                    doc = fetch_one("SELECT d.id FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.full_name LIKE %s", (f"%{doc_name}%",))
                                    if doc:
                                        from datetime import date, timedelta
                                        next_date = date.today() + timedelta(days=2)
                                        execute_query(
                                            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason) VALUES (%s, %s, %s, '10:00:00', %s)",
                                            (patient['id'], doc['id'], next_date.isoformat(), reason)
                                        )
                                        st.success(f"Auto-booked appointment with {doc_name} on {next_date} at 10:00 AM!")
                            except (json.JSONDecodeError, IndexError, KeyError):
                                pass  # Not a booking action
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.info("No API key found. Using mock response.")
                    st.markdown(f"""
                    <div style="background-color: #fffefc; padding: 28px; border-radius: 14px; border: 1px solid #efeeeb;">
                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 23px; color: #0f3e17; margin-bottom: 14px;">Hello, {user['full_name']}</p>
                        <p style="font-size: 14px; line-height: 1.5;">Based on your profile, your current health condition is: <strong>{patient.get('health_condition') or 'No condition recorded'}</strong>.</p>
                        <p style="font-size: 14px; line-height: 1.5;">You have <strong>{len(upcoming)}</strong> upcoming appointment(s). {'Your next appointment is on ' + str(upcoming[0]['appointment_date']) + ' with ' + upcoming[0]['doctor_name'] + '.' if upcoming else 'Consider booking an appointment with one of our available specialists.'}</p>
                    </div>
                    """, unsafe_allow_html=True)


def _render_analytics(patient):
    st.markdown("<div class='eyebrow'>MY ANALYTICS</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Visit Patterns</h2>", unsafe_allow_html=True)

    # Appointment status breakdown
    data = fetch_all("""
        SELECT status, COUNT(*) as count
        FROM appointments
        WHERE patient_id = %s
        GROUP BY status
    """, (patient['id'],))

    if data:
        df = pd.DataFrame(data)
        fig = px.pie(df, values='count', names='status', title='Appointment Status',
                     color_discrete_sequence=EASE_COLORS, hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(family='Inter, sans-serif', color='#222222'))
        st.plotly_chart(fig, use_container_width=True)

    # Timeline
    timeline_data = fetch_all("""
        SELECT a.appointment_date, u.full_name as doctor, s.name as specialty, a.status
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date
    """, (patient['id'],))

    if timeline_data:
        df2 = pd.DataFrame(timeline_data)
        df2['appointment_date'] = pd.to_datetime(df2['appointment_date'])
        fig2 = px.scatter(df2, x='appointment_date', y='doctor', color='status',
                          title='Appointment Timeline', size_max=15,
                          color_discrete_map={'scheduled': '#0f3e17', 'completed': '#b1dbb8', 'cancelled': '#b6ced5'})
        fig2.update_traces(marker=dict(size=14))
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(family='Inter, sans-serif', color='#222222'),
                           xaxis_title='Date', yaxis_title='Doctor')
        st.plotly_chart(fig2, use_container_width=True)

    if not data and not timeline_data:
        st.info("No appointment data to visualize yet.")
