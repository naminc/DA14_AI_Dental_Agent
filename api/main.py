import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database.database import engine
from src.database import models
from src.auth import router as auth_router
from src.chat import router as chat_router

# Create all tables
models.Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Dental AI API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
