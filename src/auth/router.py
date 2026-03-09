from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from src.database.database import get_db
from src.database.models import User
from src.auth import schemas, utils

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Kiểm tra email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký!")

    # 2. Tạo User & băm mật khẩu
    hashed_password = utils.get_password_hash(user_data.password)
    new_user = User(full_name=user_data.full_name, email=user_data.email, hashed_password=hashed_password)

    # 3. Lưu MySQL
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. Tìm user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng!")

    # 2. Kiểm tra mật khẩu
    if not utils.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng!")

    # 3. Trả về Token
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email, "user_id": user.id}, 
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "full_name": user.full_name,
        "email": user.email,
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: User = Depends(utils.get_current_user)):
    return current_user