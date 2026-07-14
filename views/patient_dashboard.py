from icons import get_svg_icon
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
    from db import fetch_all, fetch_one, execute_query
    from icons import get_svg_icon
    st.html("<div class='eyebrow'>AI CLINICAL ASSISTANT</div>")
    st.html(f"<h2 style='margin-top:0;'>{get_svg_icon('ai', size=28)} Intelligent Query</h2>")

    # Thread Management
    col1, col2 = st.columns([2, 1])
    with col1:
        # Fetch available threads
        # Group by thread_id and get the first message for the title
        existing_threads = fetch_all("SELECT thread_id, MIN(created_at) as started, (SELECT message FROM ai_threads a2 WHERE a2.thread_id = ai_threads.thread_id ORDER BY created_at ASC LIMIT 1) as first_msg FROM ai_threads WHERE patient_id = %s GROUP BY thread_id ORDER BY started DESC", (patient['id'],))
        
        thread_map = {"New Chat": "New Chat"}
        for t in existing_threads:
            preview = (t['first_msg'][:30] + '...') if t['first_msg'] and len(t['first_msg']) > 30 else (t['first_msg'] or 'Empty Chat')
            thread_map[t['thread_id']] = f"{t['started'].strftime('%b %d')} - {preview}"
            
        thread_ids = [t['thread_id'] for t in existing_threads]
        options = ["New Chat"] + thread_ids
        if 'current_thread' not in st.session_state:
            st.session_state['current_thread'] = thread_ids[0] if thread_ids else "New Chat"
        
        selected_thread = st.selectbox("Conversation", options, index=options.index(st.session_state['current_thread']) if st.session_state['current_thread'] in options else 0, format_func=lambda x: thread_map[x])
        st.session_state['current_thread'] = selected_thread
        
    with col2:
        retention_options = {'1': '1 Hour', '24': '24 Hours', '168': '7 Days', '720': '30 Days', 'infinite': 'Infinite'}
        current_ret = str(patient.get('chat_retention_hours', '1'))
        if current_ret == 'None' or current_ret == '0':
            current_ret = 'infinite'
            
        ret_keys = list(retention_options.keys())
        idx = ret_keys.index(current_ret) if current_ret in ret_keys else 0
        selected_ret = st.selectbox("Retention Policy", ret_keys, index=idx, format_func=lambda x: retention_options[x])
        
        if selected_ret != current_ret:
            db_val = None if selected_ret == 'infinite' else int(selected_ret)
            execute_query("UPDATE patients SET chat_retention_hours = %s WHERE id = %s", (db_val, patient['id']))
            st.success("Saved!")
            st.rerun()

    # Cleanup expired threads
    execute_query("DELETE FROM ai_threads WHERE expires_at IS NOT NULL AND expires_at <= NOW()")

    active_thread_id = st.session_state['current_thread']
    
    # Build System Context
    upcoming = fetch_all('''
        SELECT a.appointment_date, a.appointment_time, u.full_name as doctor_name, s.name as specialty
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
        WHERE a.patient_id = %s AND a.status = 'scheduled' AND a.appointment_date >= CURDATE()
        ORDER BY a.appointment_date
    ''', (patient['id'],))

    doctors = fetch_all('''
        SELECT u.full_name, s.name as specialty, d.id as doctor_id, d.availability
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN specialties s ON d.specialty_id = s.id
    ''')

    upcoming_text = "\n".join([f"- {a['appointment_date']} at {str(a['appointment_time'])[:5]} with {a['doctor_name']} ({a['specialty']})" for a in upcoming]) if upcoming else "No upcoming appointments."
    docs_text = "\n".join([f"- {d['full_name']} ({d['specialty']}) - Avail: {d['availability']}" for d in doctors]) if doctors else "No doctors."

    system_prompt = f"""You are an AI clinical assistant for Ease Health.
Patient: {user['full_name']}
Health Condition: {patient.get('health_condition') or 'None'}
Blood Group: {patient.get('blood_group') or 'Unknown'}

Upcoming Appointments:
{upcoming_text}

Available Doctors:
{docs_text}

If the patient asks to update their health condition (e.g. they report feeling sick, new symptoms, or existing conditions), you MUST output a JSON block exactly like this:
```json
{{"action": "update_health", "condition": "new condition string here"}}
```
If the patient asks to book an appointment, output a JSON block exactly like this:
```json
{{"action": "book", "doctor_name": "Dr. Name", "reason": "Reason"}}
```
Otherwise, respond naturally and helpfully."""

    chat_container = st.container(height=400)
    
    threads = []
    if active_thread_id != "New Chat":
        threads = fetch_all("SELECT role, message FROM ai_threads WHERE thread_id = %s AND patient_id = %s ORDER BY created_at ASC", (active_thread_id, patient['id']))

    with chat_container:
        if not threads:
            st.info("Start a new conversation! It will be saved based on your retention policy.")
        for msg in threads:
            with st.chat_message(msg['role']):
                st.markdown(msg['message'])

    prompt = st.chat_input("Ask me anything about your health or appointments...")
    
    # Auto-send initial query for new chat
    if active_thread_id == "New Chat" and not prompt:
        if st.button("Start Diagnostics & Appointment Check"):
            prompt = "What appointments do I have coming up, and what is my health status?"

    if prompt:
        import uuid
        if active_thread_id == "New Chat":
            active_thread_id = str(uuid.uuid4())
            st.session_state['current_thread'] = active_thread_id
            
        expires_sql = "NULL" if selected_ret == 'infinite' else f"DATE_ADD(NOW(), INTERVAL {selected_ret} HOUR)"
        
        # Save user msg
        execute_query(f"INSERT INTO ai_threads (thread_id, patient_id, role, message, expires_at) VALUES (%s, %s, 'user', %s, {expires_sql})", 
                      (active_thread_id, patient['id'], prompt))
                      
        # Display instantly
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    import time
                    time.sleep(1)
                    from dotenv import load_dotenv
                    import os
                    load_dotenv()
                    api_key = os.getenv("GROQ_API_KEY")
                    reply = "I'm sorry, no API key is configured. Mock reply: Your health is important to us!"
                    
                    if api_key:
                        try:
                            from langchain_groq import ChatGroq
                            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
                            llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, api_key=api_key)
                            
                            msgs = [SystemMessage(content=system_prompt)]
                            for t in threads:
                                if t['role'] == 'user': msgs.append(HumanMessage(content=t['message']))
                                else: msgs.append(AIMessage(content=t['message']))
                            msgs.append(HumanMessage(content=prompt))
                            
                            response = llm.invoke(msgs)
                            reply = response.content
                            
                            # Execute tools if found
                            if '```json' in reply:
                                try:
                                    import json
                                    j_str = reply.split('```json')[1].split('```')[0].strip()
                                    data = json.loads(j_str)
                                    if data.get('action') == 'update_health':
                                        execute_query("UPDATE patients SET health_condition = %s WHERE id = %s", (data['condition'], patient['id']))
                                        reply += "\n\n*(System: Health condition updated successfully)*"
                                    elif data.get('action') == 'book':
                                        doc_name = data.get('doctor_name', '')
                                        reason = data.get('reason', 'AI booked')
                                        doc = fetch_one("SELECT d.id FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.full_name LIKE %s", (f"%{doc_name}%",))
                                        if doc:
                                            from datetime import date, timedelta
                                            next_date = date.today() + timedelta(days=2)
                                            execute_query("INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES (%s, %s, %s, '10:00:00', %s, 'scheduled')", 
                                                          (patient['id'], doc['id'], next_date.isoformat(), reason))
                                            reply += f"\n\n*(System: Appointment booked with {doc_name} for {next_date})*"
                                except Exception as e:
                                    print("Tool error:", e)
                                    
                        except Exception as e:
                            reply = f"Error communicating with AI: {e}"
                            
                    st.markdown(reply)
                    execute_query(f"INSERT INTO ai_threads (thread_id, patient_id, role, message, expires_at) VALUES (%s, %s, 'assistant', %s, {expires_sql})", 
                                  (active_thread_id, patient['id'], reply))
        st.rerun()

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
        st.plotly_chart(fig, width='stretch')

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
        st.plotly_chart(fig2, width='stretch')

    if not data and not timeline_data:
        st.info("No appointment data to visualize yet.")
