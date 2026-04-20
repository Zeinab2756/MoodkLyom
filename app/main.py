# app/main.py
import os
import time
import sys
import traceback
import json
import whisper
import shutil
import numpy as np
import soundfile as sf

# Ensure ffmpeg is in path for Windows
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vosk import Model, KaldiRecognizer

# Database imports
from .database import Base, engine
from app.models import user, mood, task, hack  # SQLAlchemy models

# NEW: import the BERT emotional classifier
from app.models.emotion_model import emotion_classifier


# -----------------------------
# Initialize FastAPI app
# -----------------------------
app = FastAPI(
    title="MoodakLyom API",
    description="Backend for MoodakLyom Kotlin App",
    version="1.0.0"
)

# -----------------------------
# Middleware: Logging requests
# -----------------------------
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
            content={"success": False, "error": {"code": "SERVER_ERROR", "message": "Unexpected error"}}
        )


# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Initialize Database
# -----------------------------
Base.metadata.create_all(bind=engine)


# -----------------------------
# Load Models
# -----------------------------
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "vosk-small")
if os.path.exists(VOSK_MODEL_PATH):
    print(f"[INFO] Using Vosk model at: {VOSK_MODEL_PATH}")
    vosk_model = Model(VOSK_MODEL_PATH)
else:
    print(f"[WARN] Vosk model not found at {VOSK_MODEL_PATH}")

print("[INFO] Loading Whisper model...")
whisper_model = whisper.load_model("tiny")
print("[INFO] Whisper model loaded")


# -----------------------------
# /analyze — Text → Emotion
# -----------------------------
@app.post("/analyze")
async def analyze(request: dict):
    text = request.get("text", "")

    if not text or text.strip() == "":
        return {"success": False, "message": "No text provided."}

    emotion_result = emotion_classifier.predict_emotion(text)

    return {
        "success": True,
        "text": text,
        "primary_emotion": emotion_result["primary_emotion"],
        "confidence": emotion_result["confidence"],
        "alternative_emotions": emotion_result["alternative_emotions"],
        "all_probabilities": emotion_result.get("all_probabilities", {})
    }


# -----------------------------
# Include Routes
# -----------------------------
from app.routes import user as user_routes
from app.routes import mood as mood_routes
from app.routes import task as task_routes
from app.routes import resources as resources_routes
from app.routes import profile as profile_routes
from app.routes import hack as hack_routes
from app.routes import voice as voice_routes

app.include_router(user_routes.router, prefix="/user", tags=["User"])
app.include_router(mood_routes.router, prefix="/mood", tags=["Mood"])
app.include_router(task_routes.router, prefix="/tasks", tags=["Tasks"])
app.include_router(resources_routes.router, prefix="/resources", tags=["Resources"])
app.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])
app.include_router(hack_routes.router, prefix="/hacks", tags=["Hacks"])
app.include_router(voice_routes.router)


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def root():
    return {"message": "MoodakLyom Backend is running successfully!"}
