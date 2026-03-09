# src/auth/utils.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.config import SECRET_KEY, ALGORITHM
from src.database.database import get_db
from src.database.models import User

# Cấu hình Token
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY chưa được cấu hình trong file .env")

# Token sống 7 ngày (60 phút * 24 giờ * 7 ngày)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

# Schemes: Dùng bcrypt cho mật khẩu và OAuth2 cho Token
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Lưu ý: tokenUrl phải khớp với route đăng nhập thực tế của bạn
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- Xử lý mật khẩu ---
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# --- Xử lý JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    # Sử dụng thời gian hết hạn mặc định 7 ngày nếu không truyền expires_delta
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependency lấy User hiện tại ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập hết hạn hoặc không hợp lệ",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Giải mã Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Truy vấn User từ DB dựa trên email trong token
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user