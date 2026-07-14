import os
def run():
    with open("main.py", "r") as f:
        content = f.read()

    settings_idx = content.find("elif page == 'settings':")
    if settings_idx == -1: return

    end_idx = content.find("elif page == 'dashboard':")
    if end_idx == -1: return

    new_settings = """elif page == 'settings':
        st.html("<h2>Settings</h2>")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.html("<h4>Change Password</h4>")
            with st.form("change_password_form"):
                old_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
                if st.form_submit_button("Update Password", width='stretch'):
                    if not old_pw or not new_pw:
                        st.error("Please fill in all fields.")
                    else:
                        user_record = validate_password(user['email'], old_pw)
                        if user_record:
                            import re
                            if len(new_pw) < 8 or not re.search(r"[A-Z]", new_pw) or not re.search(r"\\d", new_pw) or not re.search(r"[!@#$%^&*(),.?\\":{}|<>]", new_pw):
                                st.error("Password must be at least 8 chars long and contain an uppercase letter, a number, and a special character.")
                            else:
                                import bcrypt
                                from db import execute_query
                                new_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user['id']))
                                st.success("Password updated successfully!")
                        else:
                            st.error("Incorrect current password.")

        with col2:
            if role == 'patient':
                st.html("<h4>Medical Profile</h4>")
                from db import fetch_one, execute_query
                patient = fetch_one("SELECT * FROM patients WHERE user_id = %s", (user['id'],))
                if patient:
                    with st.form("update_medical_form"):
                        blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], index=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(patient['blood_group']) if patient['blood_group'] else 0)
                        emergency = st.text_input("Emergency Contact", value=patient['emergency_contact'] or "")
                        health = st.text_area("Health Condition (Current known issues)", value=patient['health_condition'] or "")
                        
                        if st.form_submit_button("Update Profile", width='stretch'):
                            execute_query("UPDATE patients SET blood_group=%s, emergency_contact=%s, health_condition=%s WHERE id=%s", (blood, emergency, health, patient['id']))
                            st.success("Profile updated!")
    """
    
    final = content[:settings_idx] + new_settings + content[end_idx:]
    with open("main.py", "w") as f:
        f.write(final)

run()
