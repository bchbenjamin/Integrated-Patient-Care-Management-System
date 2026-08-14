from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send, Message
import uvicorn

from app.routers import auth, dashboard, ai, prescriptions, calendar_schedule, integrations, pharmacy

app = FastAPI(title="Ease Health IPCMS")

class RoleBasedSessionMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                session = scope.get("session", {})
                user = session.get("user")
                max_age = None
                if user and isinstance(user, dict) and user.get("role") == "patient":
                    max_age = 2592000

                if max_age is not None:
                    headers = message.get("headers", [])
                    new_headers = []
                    for k, v in headers:
                        if k.lower() == b"set-cookie":
                            cookie_str = v.decode("latin-1")
                            if cookie_str.startswith("session="):
                                parts = cookie_str.split("; ")
                                new_parts = [p for p in parts if not (p.lower().startswith("max-age=") or p.lower().startswith("expires="))]
                                new_parts.append(f"Max-Age={max_age}")
                                v = "; ".join(new_parts).encode("latin-1")
                        new_headers.append((k, v))
                    message["headers"] = new_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)

app.add_middleware(RoleBasedSessionMiddleware)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey", max_age=None)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(prescriptions.router)
app.include_router(calendar_schedule.router)
app.include_router(integrations.router)
app.include_router(pharmacy.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return RedirectResponse(f"/{user['role']}_dashboard")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
