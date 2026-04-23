import sys
import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, SessionLocal, engine
from app.models import hack, mood, task, user  # noqa: F401 - imported for metadata
from app.services.wellness_tips import ensure_default_hacks

app = FastAPI(
    title="Moodaak API",
    description="Backend for MoodakLyom App",
    version="1.1.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    try:
        print(f"[REQ] {request.method} {request.url.path}", flush=True)
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        print(f"[RES] {request.method} {request.url.path} -> {response.status_code} ({duration:.1f}ms)", flush=True)
        return response
    except Exception as exc:
        duration = (time.time() - start) * 1000
        print(f"[EXC] {request.method} {request.url.path} after {duration:.1f}ms", flush=True)
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"code": "SERVER_ERROR", "message": "Unexpected error"}},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    ensure_default_hacks(db)

from app.routes import (  # noqa: E402 - routers are loaded after startup-side DB initialization above
    emotion_routes,
    hack as hack_routes,
    mood as mood_routes,
    mood_routes as mood_analysis_routes,
    profile as profile_routes,
    resources as resource_routes,
    task as task_routes,
    user as user_routes,
    voice as voice_routes,
)

app.include_router(user_routes.router, prefix="/user", tags=["User"])
app.include_router(emotion_routes.router)
app.include_router(mood_routes.router, prefix="/mood", tags=["Mood"])
app.include_router(mood_analysis_routes.router)
app.include_router(task_routes.router, prefix="/tasks", tags=["Tasks"])
app.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])
app.include_router(hack_routes.router, prefix="/hacks", tags=["Hacks"])
app.include_router(resource_routes.router, prefix="/resources", tags=["Resources"])
app.include_router(voice_routes.router, prefix="/voice", tags=["Voice"])


@app.get("/")
def root():
    return {"message": "MoodakLyom backend is running successfully!", "status": "ok"}
