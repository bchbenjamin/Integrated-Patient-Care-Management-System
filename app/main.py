from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from app.routers import auth, dashboard, ai, prescriptions, calendar_schedule, integrations

app = FastAPI(title="Ease Health IPCMS")

app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(prescriptions.router)
app.include_router(calendar_schedule.router)
app.include_router(integrations.router)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return RedirectResponse(f"/{user['role']}_dashboard")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
