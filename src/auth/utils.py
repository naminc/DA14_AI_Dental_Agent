# src/auth/utils.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from src.database.database import get_db
from src.database.models import User

# Cấu hình Token
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY chưa được cấu hình trong file .env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Lấy hash mật khẩu
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Kiểm tra hash mật khẩu
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Tạo token access (JWT)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    # Nếu expires_delta không được cung cấp, sử dụng thời gian mặc định
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # Cập nhật thời gian hết hạn của token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Lấy user hiện tại
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập hết hạn hoặc không hợp lệ",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Giải mã token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Truy vấn user từ database dựa trên email trong token
    user = db.query(User).filter(User.email == email).first()
    # Nếu user không tồn tại, trả về lỗi
    if user is None:
        # Nếu user không tồn tại, trả về lỗi
        raise credentials_exception
    return user