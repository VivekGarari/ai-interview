from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import create_tables
from app.routers import auth, interview, coding, progress, ws, video, exam


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    print(f"✅ {settings.APP_NAME} started")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(interview.router)
app.include_router(coding.router)
app.include_router(progress.router)
app.include_router(ws.router)
app.include_router(video.router)
app.include_router(exam.router)


@app.api_route("/health", methods=["GET", "HEAD"], tags=["System"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}