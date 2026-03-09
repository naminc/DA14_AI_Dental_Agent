from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL

if not DATABASE_URL:
    raise ValueError("Thiếu DATABASE_URL trong file .env hoặc config.py")

# Khởi tạo Engine
engine = create_engine(DATABASE_URL)

# Tạo SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()