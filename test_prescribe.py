import asyncio
from app.routers.prescriptions import get_prescribe
from fastapi import Request

class DummySession(dict):
    pass

class DummyRequest:
    def __init__(self):
        self.session = DummySession({
            "user": {
                "id": 2, # Assuming 2 is a doctor
                "role": "doctor",
                "full_name": "Dr. Test"
            }
        })
        self.scope = {"type": "http"}
        self._headers = {}
        self._query_params = {}
        self._path_params = {}

async def test():
    req = Request(scope={"type": "http"})
    # Hack request session
    req.scope["session"] = {
        "user": {
            "id": 1, # Make sure a doctor with user_id=1 or something exists, or just catch the 404
            "role": "doctor",
            "full_name": "Dr. Test"
        }
    }
    
    # Try finding a real doctor id from db
    from app.core.db import fetch_one
    doc = fetch_one("SELECT * FROM doctors LIMIT 1")
    if doc:
        req.scope["session"]["user"]["id"] = doc["user_id"]
    
    try:
        res = await get_prescribe(req)
        print("SUCCESS")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
