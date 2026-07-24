from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Login as patient
resp = client.post("/login", data={"email": "rahul.mehta@email.com", "password": "Patient@123"})
cookie = resp.headers.get("set-cookie")
print("Login status:", resp.status_code)

# Chat
resp2 = client.post(
    "/chat", 
    json={"query": "I want to book an appointment for tomorrow at 10am for a headache. Doc ID 1"}, 
    headers={"cookie": cookie}
)
print("Chat status:", resp2.status_code)
print("Response:", resp2.json())
