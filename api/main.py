import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database.database import engine
from src.database import models
from src.auth import router as auth_router
from src.chat import router as chat_router
from src.chat.dependencies import get_chatbot

# Create all tables
models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] Đang khởi tạo DentalChatbot + load Embedding model...")
    get_chatbot()
    print("[STARTUP] Sẵn sàng nhận request.")
    yield


# FastAPI app
app = FastAPI(title="Dental AI API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.get("/")(lambda: {"message": "FastAPI is running"})

# Routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
