from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL

# Kiểm tra DATABASE_URL có tồn tại không
if not DATABASE_URL:
    raise ValueError("Thieu DATABASE_URL trong file .env")

# Tạo engine
engine = create_engine(DATABASE_URL)
# Tạo session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Tạo base
Base = declarative_base()


# Lấy database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
