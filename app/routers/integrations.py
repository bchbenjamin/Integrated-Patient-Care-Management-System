from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.db import execute_query, fetch_one
import app.services.google_calendar as gc
import app.services.google_health as gh
from datetime import datetime, timedelta
import bcrypt
import secrets
import httpx

router = APIRouter(prefix="/auth")

def save_integration(user_id: int, provider: str, tokens: dict):
    if not tokens:
        return
    
    expires_in = tokens.get('expires_in', 3600)
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    execute_query(
        """
        INSERT INTO user_integrations (user_id, provider, access_token, refresh_token, token_expires_at, scopes)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            access_token = VALUES(access_token),
            refresh_token = COALESCE(VALUES(refresh_token), refresh_token),
            token_expires_at = VALUES(token_expires_at),
            scopes = VALUES(scopes),
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            provider,
            tokens.get('access_token'),
            tokens.get('refresh_token'),
            expires_at,
            tokens.get('scope', '')
        )
    )

@router.get("/google/login")
async def google_login(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    state = "integration"
    url = gc.get_auth_url(state)
    if not url:
        return RedirectResponse("/settings?error=not_configured")
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(request: Request, code: str = None, error: str = None, state: str = None):
    if state == "patient_login":
        if not code:
            return RedirectResponse("/login?error=google_auth_failed")
        
        tokens = await gc.exchange_code(code)
        if not tokens:
            return RedirectResponse("/login?error=google_exchange_failed")
        
        access_token = tokens.get("access_token")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if resp.status_code != 200:
                return RedirectResponse("/login?error=google_profile_failed")
            user_info = resp.json()
            
        email = user_info.get("email")
        name = user_info.get("name", "Unknown")
        
        user_record = fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user_record:
            if user_record["role"] != "patient":
                return RedirectResponse("/login?error=google_login_not_available_for_staff")
            user_to_login = user_record
        else:
            random_pass = secrets.token_urlsafe(32)
            hashed = bcrypt.hashpw(random_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            execute_query(
                "INSERT INTO users (email, password_hash, full_name, role) VALUES (%s, %s, %s, 'patient')",
                (email, hashed, name)
            )
            user_to_login = fetch_one("SELECT * FROM users WHERE email = %s", (email,))
            execute_query("INSERT INTO patients (user_id) VALUES (%s)", (user_to_login["id"],))
            
        # Don't leak password hash into session
        user_to_login.pop('password_hash', None)
        for k, v in user_to_login.items():
            if hasattr(v, "isoformat"):
                user_to_login[k] = v.isoformat()
        
        request.session["user"] = user_to_login
        
        granted_scopes = tokens.get("scope", "")
        if "calendar" in granted_scopes:
            save_integration(user_to_login["id"], "google_calendar", tokens)
        if "health" in granted_scopes:
            save_integration(user_to_login["id"], "google_health", tokens)
            
        return RedirectResponse("/")

    user = request.session.get("user")
    if not user or not code:
        return RedirectResponse("/settings?error=auth_failed")
    
    tokens = await gc.exchange_code(code)
    if tokens:
        save_integration(user['id'], 'google_calendar', tokens)
        return RedirectResponse("/settings?integration=success")
    return RedirectResponse("/settings?error=exchange_failed")

@router.get("/google/health/login")
async def google_health_login(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    state = "integration"
    url = gh.get_auth_url(state)
    if not url:
        return RedirectResponse("/settings?error=not_configured")
    return RedirectResponse(url)

@router.get("/google/health/callback")
async def google_health_callback(request: Request, code: str = None, error: str = None):
    user = request.session.get("user")
    if not user or not code:
        return RedirectResponse("/settings?error=auth_failed")
    
    tokens = await gh.exchange_code(code)
    if tokens:
        save_integration(user['id'], 'google_health', tokens)
        return RedirectResponse("/settings?integration=success")
    return RedirectResponse("/settings?error=exchange_failed")
