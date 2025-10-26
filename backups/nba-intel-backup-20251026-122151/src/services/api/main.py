from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, predictions, live, clips, social

app = FastAPI(title="NBA Intel API", version="0.1.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(predictions.router, prefix="", tags=["predictions"])
app.include_router(live.router, prefix="", tags=["live"])
app.include_router(clips.router, prefix="", tags=["clips"])
app.include_router(social.router, prefix="", tags=["social"])
