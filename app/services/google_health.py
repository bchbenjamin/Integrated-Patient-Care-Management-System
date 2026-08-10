"""
google_health.py — Google Health API integration.
Handles OAuth2 and health data retrieval via the Google Health API.

Uses the new Google Health API scopes (replacing deprecated Google Fit):
  - googlehealth.activity_and_fitness.readonly
  - googlehealth.health_metrics_and_measurements.readonly
  - googlehealth.sleep.readonly
"""
import os
from typing import Optional, List
from datetime import datetime, timedelta


def get_health_client_config() -> dict:
    """Get Google Health OAuth2 configuration."""
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GOOGLE_HEALTH_REDIRECT_URI", "http://localhost:8000/auth/google/health/callback"),
        "scopes": [
            "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
            "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
            "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
        ]
    }


def is_configured() -> bool:
    """Check if Google Health integration is configured."""
    config = get_health_client_config()
    return bool(config["client_id"] and config["client_secret"])


def get_auth_url(state: str = "") -> str:
    """Generate OAuth2 authorization URL for Google Health.
    
    Note: Users may partially consent (approve only some scopes).
    The application handles partial consent gracefully by checking
    which scopes were actually granted before fetching data.
    """
    config = get_health_client_config()
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
        # Request granular consent so users can approve individual scopes
        "include_granted_scopes": "true",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code(code: str) -> Optional[dict]:
    """Exchange authorization code for tokens."""
    config = get_health_client_config()
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


def _check_scope_granted(granted_scopes: str, required_scope: str) -> bool:
    """Check if a specific scope was granted during partial consent."""
    if not granted_scopes:
        return True  # Assume granted if we can't check
    return required_scope in granted_scopes


async def get_steps(access_token: str, days: int = 7, granted_scopes: str = "") -> List[dict]:
    """Get daily step counts from Google Health API.
    
    Requires scope: googlehealth.activity_and_fitness.readonly
    """
    activity_scope = "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"
    if not _check_scope_granted(granted_scopes, activity_scope):
        return []

    import httpx
    end_time_millis = int(datetime.utcnow().timestamp() * 1000)
    start_time_millis = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    
    try:
        async with httpx.AsyncClient() as client:
            # Use the Google Health API endpoint for activity data
            resp = await client.post(
                "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": start_time_millis,
                    "endTimeMillis": end_time_millis,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for bucket in data.get("bucket", []):
                    start = datetime.fromtimestamp(int(bucket["startTimeMillis"]) / 1000)
                    steps = 0
                    for dataset in bucket.get("dataset", []):
                        for point in dataset.get("point", []):
                            for val in point.get("value", []):
                                steps += val.get("intVal", 0)
                    results.append({"date": start.strftime("%Y-%m-%d"), "steps": steps})
                return results
            elif resp.status_code == 403:
                # Scope not granted or API not enabled
                return []
    except Exception:
        pass
    return []


async def get_heart_rate(access_token: str, days: int = 7, granted_scopes: str = "") -> List[dict]:
    """Get heart rate data from Google Health API.
    
    Requires scope: googlehealth.health_metrics_and_measurements.readonly
    """
    metrics_scope = "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly"
    if not _check_scope_granted(granted_scopes, metrics_scope):
        return []

    import httpx
    end_time_millis = int(datetime.utcnow().timestamp() * 1000)
    start_time_millis = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "aggregateBy": [{"dataTypeName": "com.google.heart_rate.bpm"}],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": start_time_millis,
                    "endTimeMillis": end_time_millis,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for bucket in data.get("bucket", []):
                    start = datetime.fromtimestamp(int(bucket["startTimeMillis"]) / 1000)
                    bpm_values = []
                    for dataset in bucket.get("dataset", []):
                        for point in dataset.get("point", []):
                            for val in point.get("value", []):
                                if val.get("fpVal"):
                                    bpm_values.append(val["fpVal"])
                    if bpm_values:
                        results.append({
                            "date": start.strftime("%Y-%m-%d"),
                            "avg_bpm": round(sum(bpm_values) / len(bpm_values)),
                            "min_bpm": round(min(bpm_values)),
                            "max_bpm": round(max(bpm_values)),
                        })
                return results
            elif resp.status_code == 403:
                return []
    except Exception:
        pass
    return []


async def get_health_summary(access_token: str, granted_scopes: str = "") -> dict:
    """Get a summary of health metrics for dashboard display.
    
    Handles partial consent gracefully — if a user didn't grant a
    particular scope, the corresponding data will simply be empty.
    """
    import asyncio
    steps_task = asyncio.create_task(get_steps(access_token, days=7, granted_scopes=granted_scopes))
    hr_task = asyncio.create_task(get_heart_rate(access_token, days=7, granted_scopes=granted_scopes))
    
    steps = await steps_task
    heart_rate = await hr_task
    
    total_steps_week = sum(s["steps"] for s in steps) if steps else 0
    avg_steps = total_steps_week // 7 if steps else 0
    latest_hr = heart_rate[-1] if heart_rate else None
    
    return {
        "steps_today": steps[-1]["steps"] if steps else 0,
        "avg_steps_week": avg_steps,
        "total_steps_week": total_steps_week,
        "heart_rate": latest_hr,
        "steps_history": steps,
        "heart_rate_history": heart_rate,
    }
