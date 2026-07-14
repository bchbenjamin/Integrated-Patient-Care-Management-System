import os, time, json
def run():
    with open("views/patient_dashboard.py", "r") as f:
        content = f.read()

    # We need to completely rewrite _render_ai_assistant
    # Let's just find where it starts and ends
    start_idx = content.find("def _render_ai_assistant(patient, user):")
    end_idx = content.find("def _render_analytics(patient):")
    
    if start_idx == -1 or end_idx == -1:
        print("Could not find boundaries")
        return

    new_ai_code = """def _render_ai_assistant(patient, user):
    from db import fetch_all, fetch_one, execute_query
    st.html("<div class='eyebrow'>AI CLINICAL ASSISTANT</div>")
    st.html(f"<h2 style='margin-top:0;'>{get_svg_icon('ai', size=28)} Intelligent Query</h2>")

    # Thread Management
    col1, col2 = st.columns([2, 1])
    with col1:
        # Fetch available threads
        existing_threads = fetch_all("SELECT DISTINCT thread_id FROM ai_threads WHERE patient_id = %s", (patient['id'],))
        thread_ids = [t['thread_id'] for t in existing_threads]
        if 'current_thread' not in st.session_state:
            st.session_state['current_thread'] = thread_ids[0] if thread_ids else "New Chat"
        
        options = ["New Chat"] + thread_ids
        selected_thread = st.selectbox("Conversation", options, index=options.index(st.session_state['current_thread']) if st.session_state['current_thread'] in options else 0)
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

    upcoming_text = "\\n".join([f"- {a['appointment_date']} at {str(a['appointment_time'])[:5]} with {a['doctor_name']} ({a['specialty']})" for a in upcoming]) if upcoming else "No upcoming appointments."
    docs_text = "\\n".join([f"- {d['full_name']} ({d['specialty']}) - Avail: {d['availability']}" for d in doctors]) if doctors else "No doctors."

    system_prompt = f\"\"\"You are an AI clinical assistant for Ease Health.
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
Otherwise, respond naturally and helpfully.\"\"\"

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
                                        reply += "\\n\\n*(System: Health condition updated successfully)*"
                                    elif data.get('action') == 'book':
                                        doc_name = data.get('doctor_name', '')
                                        reason = data.get('reason', 'AI booked')
                                        doc = fetch_one("SELECT d.id FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.full_name LIKE %s", (f"%{doc_name}%",))
                                        if doc:
                                            from datetime import date, timedelta
                                            next_date = date.today() + timedelta(days=2)
                                            execute_query("INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES (%s, %s, %s, '10:00:00', %s, 'scheduled')", 
                                                          (patient['id'], doc['id'], next_date.isoformat(), reason))
                                            reply += f"\\n\\n*(System: Appointment booked with {doc_name} for {next_date})*"
                                except Exception as e:
                                    print("Tool error:", e)
                                    
                        except Exception as e:
                            reply = f"Error communicating with AI: {e}"
                            
                    st.markdown(reply)
                    execute_query(f"INSERT INTO ai_threads (thread_id, patient_id, role, message, expires_at) VALUES (%s, %s, 'assistant', %s, {expires_sql})", 
                                  (active_thread_id, patient['id'], reply))
        st.rerun()

"""
    
    final_content = content[:start_idx] + new_ai_code + content[end_idx:]
    with open("views/patient_dashboard.py", "w") as f:
        f.write(final_content)

run()
