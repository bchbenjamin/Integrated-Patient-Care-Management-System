"""
doctor_dashboard.py — Doctor Dashboard
My schedule, my patients, availability toggle, health condition editing, notes.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from db import fetch_all, fetch_one, execute_query

EASE_COLORS = ["#0f3e17", "#b1dbb8", "#b6ced5", "#cfe7d3", "#e1f4df", "#0c2f10"]


def render(user):
    # Get doctor record
    doctor = fetch_one("SELECT * FROM doctors WHERE user_id = %s", (user['id'],))
    if not doctor:
        st.error("Doctor profile not found.")
        return

    specialty = fetch_one("SELECT name FROM specialties WHERE id = %s", (doctor['specialty_id'],))
    spec_name = specialty['name'] if specialty else "General"

    st.markdown("<div class='eyebrow'>PHYSICIAN PORTAL</div>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='margin-top:0;'>{user['full_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:14px; color:#222;'>{spec_name} · {doctor['qualification'] or ''} · {doctor['experience_years'] or 0} years experience</p>", unsafe_allow_html=True)

    # Availability toggle
    avail_options = ['available', 'busy', 'off_duty']
    avail_labels = {'available': 'Available', 'busy': 'Busy', 'off_duty': 'Off Duty'}
    current_avail = doctor['availability']

    col_a, col_b = st.columns([3, 1])
    with col_a:
        new_avail = st.selectbox(
            "My Availability",
            avail_options,
            index=avail_options.index(current_avail),
            format_func=lambda x: avail_labels[x]
        )
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Update Status"):
            execute_query("UPDATE doctors SET availability = %s WHERE id = %s", (new_avail, doctor['id']))
            st.success("Availability updated!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Tabs ---
    tab_schedule, tab_patients, tab_analytics = st.tabs(["Today's Schedule", "My Patients", "Analytics"])

    with tab_schedule:
        _render_schedule(doctor)

    with tab_patients:
        _render_patients(doctor)

    with tab_analytics:
        _render_doctor_analytics(doctor)


def _render_schedule(doctor):
    st.markdown("<div class='eyebrow'>TODAY'S SCHEDULE</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Appointments</h2>", unsafe_allow_html=True)

    # Today's appointments
    today_appts = fetch_all("""
        SELECT a.id, a.appointment_date, a.appointment_time, a.status, a.reason, a.notes,
               u.full_name as patient_name, p.health_condition, p.blood_group
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = %s AND a.appointment_date = CURDATE()
        ORDER BY a.appointment_time
    """, (doctor['id'],))

    if today_appts:
        for appt in today_appts:
            time_str = str(appt['appointment_time'])[:5] if appt['appointment_time'] else ''
            status_txt = {'scheduled': '[SCHEDULED]', 'completed': '[COMPLETED]', 'cancelled': '[CANCELLED]'}.get(appt['status'], '')

            with st.expander(f"{status_txt} {time_str} — {appt['patient_name']}"):
                st.write(f"**Reason:** {appt['reason'] or 'N/A'}")
                st.write(f"**Health Condition:** {appt['health_condition'] or 'N/A'}")
                st.write(f"**Blood Group:** {appt['blood_group'] or 'N/A'}")

                if appt['status'] == 'scheduled':
                    notes = st.text_area("Add Notes", value=appt['notes'] or "", key=f"note_{appt['id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Complete", key=f"comp_{appt['id']}"):
                            execute_query(
                                "UPDATE appointments SET status='completed', notes=%s WHERE id=%s",
                                (notes, appt['id'])
                            )
                            st.success("Marked as completed!")
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_{appt['id']}"):
                            execute_query("UPDATE appointments SET status='cancelled' WHERE id=%s", (appt['id'],))
                            st.warning("Appointment cancelled.")
                            st.rerun()
                elif appt['notes']:
                    st.write(f"**Notes:** {appt['notes']}")
    else:
        st.info("No appointments scheduled for today.")

    # Upcoming
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>UPCOMING</div>", unsafe_allow_html=True)

    upcoming = fetch_all("""
        SELECT a.appointment_date, a.appointment_time, a.reason, u.full_name as patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = %s AND a.appointment_date > CURDATE() AND a.status = 'scheduled'
        ORDER BY a.appointment_date, a.appointment_time
        LIMIT 10
    """, (doctor['id'],))

    if upcoming:
        df = pd.DataFrame(upcoming)
        df['appointment_date'] = pd.to_datetime(df['appointment_date']).dt.strftime('%Y-%m-%d')
        df['appointment_time'] = df['appointment_time'].apply(lambda x: str(x)[:5] if x else '')
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No upcoming appointments.")


def _render_patients(doctor):
    st.markdown("<div class='eyebrow'>MY PATIENTS</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Patient Records</h2>", unsafe_allow_html=True)

    patients = fetch_all("""
        SELECT DISTINCT p.id, u.full_name, u.email, p.blood_group, p.health_condition, p.gender, p.date_of_birth
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = %s
        ORDER BY u.full_name
    """, (doctor['id'],))

    for pat in patients:
        with st.expander(f"{pat['full_name']} — {pat['blood_group'] or 'N/A'}"):
            st.write(f"**Email:** {pat['email']}")
            st.write(f"**Gender:** {pat['gender'] or 'N/A'} | **DOB:** {pat['date_of_birth'] or 'N/A'}")

            new_condition = st.text_area(
                "Health Condition (editable by you)",
                value=pat['health_condition'] or "",
                key=f"doc_cond_{pat['id']}"
            )
            if st.button("Save Condition", key=f"doc_save_{pat['id']}"):
                execute_query("UPDATE patients SET health_condition = %s WHERE id = %s", (new_condition, pat['id']))
                st.success("Health condition updated!")
                st.rerun()


def _render_doctor_analytics(doctor):
    st.markdown("<div class='eyebrow'>MY ANALYTICS</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:0;'>Practice Overview</h2>", unsafe_allow_html=True)

    # Weekly load
    data = fetch_all("""
        SELECT appointment_date, COUNT(*) as count
        FROM appointments
        WHERE doctor_id = %s
        GROUP BY appointment_date
        ORDER BY appointment_date
    """, (doctor['id'],))

    if data:
        df = pd.DataFrame(data)
        df['appointment_date'] = pd.to_datetime(df['appointment_date'])
        fig = px.bar(df, x='appointment_date', y='count', title='Appointment History',
                     color_discrete_sequence=['#0f3e17'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(family='Inter, sans-serif', color='#222222'),
                          xaxis_title='Date', yaxis_title='Appointments')
        st.plotly_chart(fig, use_container_width=True)

    # Status breakdown
    status_data = fetch_all("""
        SELECT status, COUNT(*) as count
        FROM appointments
        WHERE doctor_id = %s
        GROUP BY status
    """, (doctor['id'],))

    if status_data:
        df2 = pd.DataFrame(status_data)
        fig2 = px.pie(df2, values='count', names='status', title='Appointment Status Breakdown',
                      color_discrete_sequence=EASE_COLORS, hole=0.4)
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           font=dict(family='Inter, sans-serif', color='#222222'))
        st.plotly_chart(fig2, use_container_width=True)
