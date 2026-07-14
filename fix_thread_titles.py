import os
def run():
    with open("views/patient_dashboard.py", "r") as f:
        content = f.read()

    # Replace thread_ids = [t['thread_id'] for t in existing_threads]
    # with a better query that gets the first message
    
    old_query = """existing_threads = fetch_all("SELECT DISTINCT thread_id FROM ai_threads WHERE patient_id = %s", (patient['id'],))
        thread_ids = [t['thread_id'] for t in existing_threads]"""
        
    new_query = """# Group by thread_id and get the first message for the title
        existing_threads = fetch_all("SELECT thread_id, MIN(created_at) as started, (SELECT message FROM ai_threads a2 WHERE a2.thread_id = ai_threads.thread_id ORDER BY created_at ASC LIMIT 1) as first_msg FROM ai_threads WHERE patient_id = %s GROUP BY thread_id ORDER BY started DESC", (patient['id'],))
        
        thread_map = {"New Chat": "New Chat"}
        for t in existing_threads:
            preview = (t['first_msg'][:30] + '...') if t['first_msg'] and len(t['first_msg']) > 30 else (t['first_msg'] or 'Empty Chat')
            thread_map[t['thread_id']] = f"{t['started'].strftime('%b %d')} - {preview}"
            
        options = ["New Chat"] + [t['thread_id'] for t in existing_threads]"""

    content = content.replace(old_query, new_query)
    
    # Also update the selectbox to use format_func
    old_sel = """selected_thread = st.selectbox("Conversation", options, index=options.index(st.session_state['current_thread']) if st.session_state['current_thread'] in options else 0)"""
    new_sel = """selected_thread = st.selectbox("Conversation", options, index=options.index(st.session_state['current_thread']) if st.session_state['current_thread'] in options else 0, format_func=lambda x: thread_map[x])"""
    
    content = content.replace(old_sel, new_sel)

    with open("views/patient_dashboard.py", "w") as f:
        f.write(content)

run()
