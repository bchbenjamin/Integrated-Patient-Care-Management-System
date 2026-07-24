import os
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.core.db import fetch_all, fetch_one, execute_query

router = APIRouter()

# --- AI Tool Classes ---

class PatientAITools:
    @staticmethod
    @tool
    def get_specialties() -> str:
        """Get a list of all medical specialties available in the clinic."""
        specs = fetch_all("SELECT id, name, description FROM specialties")
        if not specs:
            return "No specialties found."
        return "\n".join([f"ID: {s['id']} | Name: {s['name']} - {s['description']}" for s in specs])

    @staticmethod
    @tool
    def get_doctors_by_specialty(specialty_id: int) -> str:
        """Find all doctors available for a specific specialty ID."""
        docs = fetch_all("SELECT d.id, u.full_name, d.qualification FROM doctors d JOIN users u ON d.user_id = u.id WHERE d.specialty_id = %s", (specialty_id,))
        if not docs:
            return f"No doctors found for specialty ID {specialty_id}."
        return "\n".join([f"Doc ID: {d['id']} | Name: {d['full_name']} | Qual: {d['qualification']}" for d in docs])

    @staticmethod
    @tool
    def draft_appointment(patient_id: int, doctor_id: int, date: str, time: str, reason: str = "General Checkup") -> str:
        """Draft an appointment. Date format: YYYY-MM-DD. Time format: HH:MM:SS."""
        import json
        doc = fetch_one("SELECT u.full_name, s.name as specialty FROM doctors d JOIN users u ON d.user_id = u.id JOIN specialties s ON d.specialty_id = s.id WHERE d.id = %s", (doctor_id,))
        if not doc:
            return f"Error: Doctor ID {doctor_id} does not exist. Please use get_specialties and get_doctors_by_specialty to find a valid doctor ID."
            
        doc_name = doc['full_name']
        
        payload = {
            "action": "confirm_appointment",
            "doctor_id": doctor_id,
            "doctor_name": doc_name,
            "date": date,
            "time": time,
            "reason": reason
        }
        return f"**ACTION_REQUIRED**\n```json\n{json.dumps(payload)}\n```"

    @staticmethod
    @tool
    def update_health_condition(patient_id: int, new_condition: str) -> str:
        """Update the patient's recorded health condition or symptoms."""
        try:
            execute_query("UPDATE patients SET health_condition = %s WHERE id = %s", (new_condition, patient_id))
            return "Health condition updated successfully."
        except Exception as e:
            return f"Failed to update health condition: {str(e)}"

    @staticmethod
    @tool
    def update_preferences(patient_id: int, new_preferences: str) -> str:
        """Update the patient's recorded preferences (e.g., preferred doctor, time, language)."""
        try:
            execute_query("UPDATE patients SET preferences = %s WHERE id = %s", (new_preferences, patient_id))
            return "Preferences updated successfully."
        except Exception as e:
            return f"Failed to update preferences: {str(e)}"

patient_tools = [
    PatientAITools.get_specialties, 
    PatientAITools.get_doctors_by_specialty, 
    PatientAITools.draft_appointment, 
    PatientAITools.update_health_condition,
    PatientAITools.update_preferences
]

# Initialize LLM
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)
llm_patient_with_tools = llm.bind_tools(patient_tools)

# --- Routes ---

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
async def chat_endpoint(request: Request, payload: ChatRequest):
    user = request.session.get("user")
    if not user or user['role'] != 'patient':
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    patient = fetch_one("SELECT id, health_condition, preferences, gender, date_of_birth FROM patients WHERE user_id = %s", (user['id'],))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    import datetime
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    prefs = patient.get('preferences') or "No preferences recorded yet."

    sys_msg = SystemMessage(content=f"""
You are the AI Clinical Assistant for Ease Health.
You are helping the patient: {user['full_name']}
Their internal Patient ID is: {patient['id']}
Their current health condition on file is: {patient['health_condition']}
Their recorded preferences: {prefs}
Today's Date: {today}

CRITICAL RULES:
- You may ask a FEW follow-ups (e.g., preferred time or doctor) to be helpful. 
- However, if the user ignores the question, denies it, or doesn't answer clearly, DO NOT push it. Immediately fall back to defaults (e.g. assume {tomorrow} at 10:00:00, or pick a random doctor via get_doctors_by_specialty) and draft the appointment.
- Use the `draft_appointment` tool to create the appointment proposal.
- DO NOT tell the user that you have successfully booked their appointment. You MUST tell them that you have "drafted" it and that they need to click the confirm button.
- Learn from the user! If they state a preference (e.g., "I like morning appointments", "I prefer Dr. Smith"), use the `update_preferences` tool to save it.
- NEVER output raw JSON, tool call arguments, database IDs, or pipe-separated lists to the user, EXCEPT when a tool returns an **ACTION_REQUIRED** JSON block. 
- If a tool returns **ACTION_REQUIRED**, you MUST copy the exact `**ACTION_REQUIRED**\n```json\n...\n``` ` text into your final response so the UI can render the form. Say a brief, polite message (e.g. "Here is your appointment draft, please confirm below:") and append the ACTION_REQUIRED block at the end.
- If you successfully update their health condition/preferences, include "**RELOAD**" anywhere in your final response so the dashboard refreshes.
""")

    messages = [sys_msg, HumanMessage(content=payload.query)]
    
    # Simple Agent Loop (Max 5 steps to prevent infinite tool loops)
    for _ in range(5):
        ai_msg = llm_patient_with_tools.invoke(messages)
        messages.append(ai_msg)
        
        if not ai_msg.tool_calls:
            reload = "**RELOAD**" in ai_msg.content
            reply = ai_msg.content.replace("**RELOAD**", "").strip()
            return {"reply": reply, "reload": reload}
            
        # Execute tools
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            tool_res = ""
            if tool_name == "get_specialties":
                tool_res = PatientAITools.get_specialties.invoke(tool_args)
            elif tool_name == "get_doctors_by_specialty":
                tool_res = PatientAITools.get_doctors_by_specialty.invoke(tool_args)
            elif tool_name == "draft_appointment":
                # Security: Force the patient_id to be the logged-in patient
                tool_args["patient_id"] = patient['id']
                tool_res = PatientAITools.draft_appointment.invoke(tool_args)
            elif tool_name == "update_health_condition":
                tool_args["patient_id"] = patient['id']
                tool_res = PatientAITools.update_health_condition.invoke(tool_args)
                
            messages.append(ToolMessage(content=tool_res, tool_call_id=tool_call["id"]))

    return {"reply": "I'm sorry, I encountered an error while processing your request. Please try again later."}

class DoctorAITools:
    @staticmethod
    @tool
    def get_doctor_patients(doctor_id: int) -> str:
        """Get a list of all patients assigned to the doctor."""
        patients = fetch_all("""
            SELECT DISTINCT p.id, u.full_name 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            JOIN users u ON p.user_id = u.id 
            WHERE a.doctor_id = %s
        """, (doctor_id,))
        if not patients:
            return "No patients found."
        return "\n".join([f"Patient ID: {p['id']} | Name: {p['full_name']}" for p in patients])

    @staticmethod
    @tool
    def draft_prescription_ai(patient_id: int, doctor_id: int, medicine_name: str, dosage: str, frequency: str, duration_days: int) -> str:
        """Drafts a prescription. IMPORTANT: Never make up medication names, dosage, or frequency without confirming with the user."""
        import json
        pat = fetch_one("SELECT u.full_name FROM patients p JOIN users u ON p.user_id = u.id WHERE p.id = %s", (patient_id,))
        if not pat:
            return f"Error: Patient ID {patient_id} does not exist. Please use get_doctor_patients to find a valid patient ID."
            
        payload = {
            "action": "confirm_prescription",
            "patient_id": patient_id,
            "patient_name": pat['full_name'],
            "medicine_name": medicine_name,
            "dosage": dosage,
            "frequency": frequency,
            "duration_days": duration_days
        }
        return f"**ACTION_REQUIRED**\n```json\n{json.dumps(payload)}\n```"

doctor_tools = [DoctorAITools.get_doctor_patients, DoctorAITools.draft_prescription_ai]
llm_doctor_with_tools = llm.bind_tools(doctor_tools)

@router.post("/doctor_chat")
async def doctor_chat_endpoint(request: Request, payload: ChatRequest):
    user = request.session.get("user")
    if not user or user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    doctor = fetch_one("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    sys_msg = SystemMessage(content=f"""
You are the AI Clinical Assistant for Ease Health.
You are helping the doctor: {user['full_name']}
Their internal Doctor ID is: {doctor['id']}

CRITICAL RULES:
- Your job is to assist them in prescribing medications or retrieving patient info.
- Use `get_doctor_patients` to find a patient ID by name if the doctor asks to prescribe to someone.
- Use `draft_prescription_ai` to draft a prescription. (Always use the doctor's internal Doctor ID {doctor['id']}).
- DO NOT tell the doctor that you have successfully prescribed the medication. You MUST tell them that you have "drafted" it and that they need to click the confirm button.
- NEVER output raw JSON, tool call arguments, database IDs, or pipe-separated lists to the doctor EXCEPT when returning an **ACTION_REQUIRED** block. ALWAYS format data into natural, conversational language.
- If a tool returns **ACTION_REQUIRED**, you MUST copy the exact `**ACTION_REQUIRED**\n```json\n...\n``` ` text into your final response so the UI can render the form. Say a brief message and append the block.
""")

    messages = [sys_msg, HumanMessage(content=payload.query)]
    
    for _ in range(5):
        ai_msg = llm_doctor_with_tools.invoke(messages)
        messages.append(ai_msg)
        
        if not ai_msg.tool_calls:
            reload = "**RELOAD**" in ai_msg.content
            reply = ai_msg.content.replace("**RELOAD**", "").strip()
            return {"reply": reply, "reload": reload}
            
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            tool_res = ""
            if tool_name == "get_doctor_patients":
                tool_args["doctor_id"] = doctor['id']
                tool_res = DoctorAITools.get_doctor_patients.invoke(tool_args)
            elif tool_name == "draft_prescription_ai":
                tool_args["doctor_id"] = doctor['id']
                tool_res = DoctorAITools.draft_prescription_ai.invoke(tool_args)
                
            messages.append(ToolMessage(content=tool_res, tool_call_id=tool_call["id"]))

    return {"reply": "Error processing request.", "reload": False}
