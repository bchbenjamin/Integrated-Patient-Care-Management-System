"""
google_calendar.py — Google Calendar API integration service.
Handles OAuth2 flow and calendar event sync.
"""
import os
from typing import Optional, List
from datetime import datetime, timedelta


def get_google_client_config() -> dict:
    """Get Google OAuth2 client configuration from environment."""
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"),
        "scopes": [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
        ]
    }


def is_configured() -> bool:
    """Check if Google Calendar integration is configured."""
    config = get_google_client_config()
    return bool(config["client_id"] and config["client_secret"])


def get_auth_url(state: str = "") -> str:
    """Generate Google OAuth2 authorization URL."""
    config = get_google_client_config()
    if not is_configured():
        return ""
    
    from urllib.parse import urlencode
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(config["scopes"]),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code(code: str) -> Optional[dict]:
    """Exchange authorization code for tokens."""
    config = get_google_client_config()
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "redirect_uri": config["redirect_uri"],
                    "grant_type": "authorization_code",
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


async def refresh_access_token(refresh_token: str) -> Optional[dict]:
    """Refresh an expired access token."""
    config = get_google_client_config()
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "grant_type": "refresh_token",
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


async def list_events(access_token: str, time_min: str = "", time_max: str = "") -> List[dict]:
    """List events from user's primary Google Calendar."""
    import httpx
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    if not time_max:
        time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": 50,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", [])
    except Exception:
        pass
    return []


async def create_event(access_token: str, event_data: dict) -> Optional[dict]:
    """Create an event on user's primary Google Calendar."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=event_data
            )
            if resp.status_code in (200, 201):
                return resp.json()
    except Exception:
        pass
    return None


async def push_appointment_to_google(access_token: str, appointment: dict) -> Optional[dict]:
    """Convert an IPCMS appointment to a Google Calendar event and push it."""
    event = {
        "summary": f"Medical Appointment - {appointment.get('reason', 'Checkup')}",
        "description": f"Appointment via Ease Health IPCMS\nStatus: {appointment.get('status', 'scheduled')}",
        "start": {
            "dateTime": f"{appointment['appointment_date']}T{appointment['appointment_time']}",
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": f"{appointment['appointment_date']}T{appointment['appointment_time']}",
            "timeZone": "Asia/Kolkata",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 30},
                {"method": "email", "minutes": 60},
            ],
        },
    }
    # Add 30 minutes to end time
    try:
        start_parts = appointment['appointment_time'].split(':')
        end_hour = int(start_parts[0])
        end_min = int(start_parts[1]) + 30
        if end_min >= 60:
            end_hour += 1
            end_min -= 60
        event["end"]["dateTime"] = f"{appointment['appointment_date']}T{end_hour:02d}:{end_min:02d}:00"
    except (IndexError, ValueError):
        pass
    
    return await create_event(access_token, event)
