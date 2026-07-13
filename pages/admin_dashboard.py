"""
admin_dashboard.py — Admin Console
Full oversight: metrics, create doctors, manage patients, analytics.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from db import fetch_all, fetch_one, execute_query
from auth import create_doctor

# Ease Health palette for Plotly charts
EASE_COLORS = ["#0f3e17", "#b1dbb8", "#b6ced5", "#cfe7d3", "#e1f4df", "#0c2f10"]


def render(user):
    st.markdown("<div class='eyebrow'>ADMIN CONSOLE</div>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='margin-top:0;'>Welcome, {user['full_name']}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:14px; color:#222;'>Full oversight of the Integrated Patient Care Management System.</p>", unsafe_allow_html=True)

    # --- Metrics Row ---
    patients = fetch_all("SELECT COUNT(*) as cnt FROM patients")
    doctors = fetch_all("SELECT COUNT(*) as cnt FROM doctors")
    appointments = fetch_all("SELECT COUNT(*) as cnt FROM appointments")
    upcoming = fetch_all("SELECT COUNT(*) as cnt FROM appointments WHERE status='scheduled' AND appointment_date >= CURDATE()")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Patients", patients[0]['cnt'])
    m2.metric("Doctors", doctors[0]['cnt'])
    m3.metric("Appointments", appointments[0]['cnt'])
    m4.metric("Upcoming", upcoming[0]['cnt'])

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Tabs ---
    tab_analytics, tab_create_doctor, tab_availability, tab_specialties, tab_records, tab_all_appts = st.tabs(
        ["Analytics", "Create Doctor", "Availability", "Specialties", "Records", "All Appointments"]
    )

    with tab_analytics:
        _render_analytics()

    with tab_create_doctor:
        _render_create_doctor()

    with tab_availability:
        _render_availability()

    with tab_specialties:
        _render_specialties()

    with tab_records:
        _render_records()

    with tab_all_appts:
        _render_all_appointments()


def _render_analytics():
    st.markdown("<div class='eyebrow'>ANALYTICS</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>System Overview</h2>", unsafe_allow_html=True)

    # Appointments by specialty
    data = fetch_all("""
        SELECT s.name as specialty, COUNT(a.id) as count
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN specialties s ON d.specialty_id = s.id
        GROUP BY s.name
    """)
    if data:
        df = pd.DataFrame(data)
        fig = px.pie(df, values='count', names='specialty', title='Appointments by Specialty',
                     color_discrete_sequence=EASE_COLORS, hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(family='Inter, sans-serif', color='#222222'))
        st.plotly_chart(fig, use_container_width=True)

    # Appointments over time
    data2 = fetch_all("""
        SELECT appointment_date, COUNT(*) as count
        FROM appointments
        GROUP BY appointment_date
        ORDER BY appointment_date
    """)
    if data2:
        df2 = pd.DataFrame(data2)
        fig2 = px.area(df2, x='appointment_date', y='count', title='Appointments Over Time',
                       color_discrete_sequence=['#0f3e17'])
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(family='Inter, sans-serif', color='#222222'),
                           xaxis_title='Date', yaxis_title='Count')
        st.plotly_chart(fig2, use_container_width=True)

    # Doctor workload
    data3 = fetch_all("""
        SELECT u.full_name as doctor, COUNT(a.id) as appointments
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        GROUP BY u.full_name
    """)
    if data3:
        df3 = pd.DataFrame(data3)
        fig3 = px.bar(df3, x='appointments', y='doctor', orientation='h', title='Doctor Workload',
                      color_discrete_sequence=['#b1dbb8'])
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(family='Inter, sans-serif', color='#222222'))
        st.plotly_chart(fig3, use_container_width=True)


def _render_create_doctor():
    st.markdown("<div class='eyebrow'>CREATE DOCTOR</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Add New Physician</h2>", unsafe_allow_html=True)

    specialties = fetch_all("SELECT id, name FROM specialties ORDER BY name")
    spec_options = {s['name']: s['id'] for s in specialties}

    with st.form("create_doctor_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *")
            email = st.text_input("Email *")
            password = st.text_input("Password *", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
        with col2:
            phone = st.text_input("Phone")
            specialty = st.selectbox("Specialty *", list(spec_options.keys()))
            qualification = st.text_input("Qualification")

        col3, col4 = st.columns(2)
        with col3:
            experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=1)
        with col4:
            bio = st.text_area("Bio", height=100)

        submitted = st.form_submit_button("Create Doctor")
        if submitted:
            if not full_name or not email or not password:
                st.error("Please fill in all required fields.")
            else:
                success, msg = create_doctor(
                    email=email, password=password, full_name=full_name, phone=phone,
                    specialty_id=spec_options[specialty], qualification=qualification,
                    experience_years=experience, bio=bio
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)


def _render_availability():
    st.markdown("<div class='eyebrow'>DOCTOR AVAILABILITY</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Manage Availability</h2>", unsafe_allow_html=True)

    doctors = fetch_all("""
        SELECT d.id, u.full_name, s.name as specialty, d.availability
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        ORDER BY u.full_name
    """)

    for doc in doctors:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{doc['full_name']}** — {doc['specialty'] or 'General'}")
        with col2:
            new_status = st.text_input(
                "Status / Timings",
                value=doc['availability'] if doc['availability'] else "",
                key=f"avail_{doc['id']}"
            )
        with col3:
            if st.button("Update", key=f"upd_avail_{doc['id']}"):
                execute_query("UPDATE doctors SET availability = %s WHERE id = %s", (new_status, doc['id']))
                st.success("Updated!")
                st.rerun()
        st.markdown("<hr style='border: none; border-top: 1px solid #efeeeb;'>", unsafe_allow_html=True)


def _render_specialties():
    st.markdown("<div class='eyebrow'>SPECIALTIES</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Medical Specialties</h2>", unsafe_allow_html=True)

    specialties = fetch_all("SELECT * FROM specialties ORDER BY name")
    for spec in specialties:
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:11px; margin-bottom:7px;'><span style='width:24px; height:24px; display:inline-block;'>{spec['icon']}</span> <strong style='font-size:16px;'>{spec['name']}</strong> — {spec['description']}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Add New Specialty"):
        with st.form("add_spec_form"):
            col1, col2 = st.columns([2, 3])
            with col1:
                name = st.text_input("Name")
            with col2:
                desc = st.text_input("Description")
            icon = st.text_area("Icon (SVG XML Code)")
            if st.form_submit_button("Add"):
                if name:
                    execute_query("INSERT INTO specialties (name, description, icon) VALUES (%s, %s, %s)", (name, desc, icon))
                    st.success(f"Added {name}!")
                    st.rerun()


def _render_records():
    st.markdown("<div class='eyebrow'>PATIENT RECORDS</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>All Patients</h2>", unsafe_allow_html=True)

    patients = fetch_all("""
        SELECT p.id, u.full_name, u.email, p.blood_group, p.health_condition, p.gender
        FROM patients p
        JOIN users u ON p.user_id = u.id
        ORDER BY u.full_name
    """)

    for pat in patients:
        with st.expander(f"{pat['full_name']} — {pat['email']}"):
            st.write(f"**Gender:** {pat['gender'] or 'N/A'} | **Blood Group:** {pat['blood_group'] or 'N/A'}")
            new_condition = st.text_area(
                "Health Condition",
                value=pat['health_condition'] or "",
                key=f"cond_{pat['id']}"
            )
            if st.button("Update Condition", key=f"upd_cond_{pat['id']}"):
                execute_query("UPDATE patients SET health_condition = %s WHERE id = %s", (new_condition, pat['id']))
                st.success("Health condition updated!")
                st.rerun()


def _render_all_appointments():
    st.markdown("<div class='eyebrow'>ALL APPOINTMENTS</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Appointment Registry</h2>", unsafe_allow_html=True)

    appts = fetch_all("""
        SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.reason,
               up.full_name as patient_name, ud.full_name as doctor_name, s.name as specialty
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users up ON p.user_id = up.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users ud ON d.user_id = ud.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """)

    if appts:
        df = pd.DataFrame(appts)
        df['appointment_date'] = pd.to_datetime(df['appointment_date']).dt.strftime('%Y-%m-%d')
        df['appointment_time'] = df['appointment_time'].apply(lambda x: str(x)[:5] if x else '')
        st.dataframe(
            df[['patient_name', 'doctor_name', 'specialty', 'appointment_date', 'appointment_time', 'status', 'reason']],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No appointments yet.")
