import io
import base64
from datetime import timedelta

import pyotp
import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.config import SECRET_KEY, ALGORITHM
from src.database.database import get_db
from src.database.models import User
from src.auth import schemas, utils

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Helper Functions

# Tạo QR code base64
def _generate_qr_base64(otpauth_uri: str) -> str:
    """Tạo QR code SVG → base64."""
    img = qrcode.make(otpauth_uri, image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# Format secret
def _format_secret(secret: str) -> str:
    """Format secret."""
    return " ".join(secret[i : i + 4] for i in range(0, len(secret), 4))


# Xây dựng response token
def _build_token_response(user: User) -> dict:
    """Xây dựng response token."""
    access_token = utils.create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "full_name": user.full_name,
        "email": user.email,
    }



# Đăng ký
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký!")

    hashed_password = utils.get_password_hash(user_data.password)
    new_user = User(full_name=user_data.full_name, email=user_data.email, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Đăng nhập
@router.post("/login")
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not utils.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng!")

    if user.is_2fa_enabled and user.totp_secret:
        temp_token = utils.create_access_token(
            data={"sub": user.email, "user_id": user.id, "purpose": "2fa_verify"},
            expires_delta=timedelta(minutes=5),
        )
        return {"requires_2fa": True, "temp_token": temp_token}

    return _build_token_response(user)



# Lấy thông tin người dùng hiện tại
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: User = Depends(utils.get_current_user)):
    return current_user


# Cập nhật thông tin người dùng
@router.put("/update-profile", response_model=schemas.UserResponse)
def update_profile(
    data: schemas.UpdateProfileRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    if not data.full_name.strip():
        raise HTTPException(status_code=400, detail="Họ và tên không được để trống!")
    if len(data.full_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Họ và tên phải có ít nhất 2 ký tự!")

    current_user.full_name = data.full_name.strip()
    db.commit()
    db.refresh(current_user)
    return current_user


# Đổi mật khẩu
@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    data: schemas.ChangePasswordRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    if not utils.verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng!")

    current_user.hashed_password = utils.get_password_hash(data.new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công!"}


# Lấy trạng thái 2FA
@router.get("/2fa/status")
def get_2fa_status(current_user: User = Depends(utils.get_current_user)):
    return {"is_enabled": bool(current_user.is_2fa_enabled)}


# Thiết lập 2FA
@router.post("/2fa/setup", response_model=schemas.TwoFactorSetupResponse)
def setup_2fa(
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Tạo TOTP secret mới + QR code. Chưa bật 2FA cho đến khi verify."""
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA đã được bật rồi!")

    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    db.commit()

    totp = pyotp.TOTP(secret)
    otpauth_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Dental AI",
    )
    qr_code = _generate_qr_base64(otpauth_uri)

    return {
        "secret": _format_secret(secret),
        "qr_code": qr_code,
    }


# Xác thực và bật 2FA
@router.post("/2fa/verify")
def verify_and_enable_2fa(
    data: schemas.TwoFactorCodeRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Xác thực mã TOTP lần đầu."""
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA đã được bật rồi!")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Chưa thiết lập 2FA. Hãy gọi /2fa/setup trước.")

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="Mã xác thực không đúng hoặc đã hết hạn!")

    current_user.is_2fa_enabled = True
    db.commit()
    return {"message": "Đã bật xác thực hai yếu tố thành công!"}


# Tắt 2FA
@router.post("/2fa/disable")
def disable_2fa(
    data: schemas.TwoFactorCodeRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Tắt 2FA — yêu cầu mã TOTP hiện tại để xác nhận."""
    if not current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA chưa được bật!")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Chưa thiết lập 2FA. Hãy gọi /2fa/setup trước.")

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="Mã xác thực không đúng!")

    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    db.commit()
    return {"message": "Đã tắt xác thực hai yếu tố!"}


# Xác thực đăng nhập 2FA
@router.post("/2fa/login-verify")
def verify_2fa_login(data: schemas.TwoFactorLoginRequest, db: Session = Depends(get_db)):
    """Bước 2 của login khi 2FA đang bật: xác thực mã TOTP + trả token thật."""
    try:
        payload = jwt.decode(data.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "2fa_verify":
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        email: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token hết hạn. Vui lòng đăng nhập lại.")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_2fa_enabled or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Yêu cầu không hợp lệ")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.totp_code, valid_window=1):
        raise HTTPException(status_code=401, detail="Mã xác thực không đúng hoặc đã hết hạn!")

    return _build_token_response(user)
