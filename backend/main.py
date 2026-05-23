import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.database import init_db
from backend.routes.screen import router as screen_router
from backend.routes.report import router as report_router
from backend.routes.stripe_routes import router as stripe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        print("[DB] Database initialized.", flush=True)
    except Exception as exc:
        print(f"[DB] init_db failed (non-fatal): {exc}", flush=True)
    yield


app = FastAPI(
    title="VisaScreenAI API",
    description="AI-powered social media screening for US visa applicants",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_env = os.getenv("CORS_ORIGINS", os.getenv("FRONTEND_URL", "http://localhost:3000"))
allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
for _dev in ["http://localhost:3000", "http://127.0.0.1:3000"]:
    if _dev not in allowed_origins:
        allowed_origins.append(_dev)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screen_router, prefix="/api")
app.include_router(report_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "VisaScreenAI API"}
