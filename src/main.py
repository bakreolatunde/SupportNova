from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from database.session import init_db
from src.api import routes_complaints, routes_admin, routes_auth, routes_dashboard

app = FastAPI(title="SupportNova", version="0.1.0")
app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(routes_complaints.router)
app.include_router(routes_admin.router)
app.include_router(routes_auth.router)
app.include_router(routes_dashboard.router)


@app.get("/")
def root():
    return RedirectResponse(url="/login-page")


@app.get("/health")
def health():
    return {"status": "ok"}
