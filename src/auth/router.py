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

def _generate_qr_base64(otpauth_uri: str) -> str:
    """Tạo QR code SVG → base64."""
    img = qrcode.make(otpauth_uri, image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _format_secret(secret: str) -> str:
    """ABCD EFGH IJKL MNOP."""
    return " ".join(secret[i : i + 4] for i in range(0, len(secret), 4))


def _build_token_response(user: User) -> dict:
    """Tạo JWT access token + response dict."""
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


# Register & Login

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra email đã tồn tại chưa
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    # Nếu email đã tồn tại, trả về lỗi
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký!")

    # Hash mật khẩu
    hashed_password = utils.get_password_hash(user_data.password)
    # Tạo user mới
    new_user = User(full_name=user_data.full_name, email=user_data.email, hashed_password=hashed_password)

    # Thêm user mới vào database
    db.add(new_user)
    # Commit transaction
    db.commit()
    # Refresh user
    db.refresh(new_user)
    # Trả về user mới
    return new_user


@router.post("/login")
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # Kiểm tra email đã tồn tại chưa
    user = db.query(User).filter(User.email == user_data.email).first()
    # Nếu email không tồn tại hoặc mật khẩu không đúng, trả về lỗi
    if not user or not utils.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng!")

    # Nếu 2FA đang bật, trả temp_token, yêu cầu xác thực bước 2
    if user.is_2fa_enabled and user.totp_secret:
        # Tạo temp_token
        temp_token = utils.create_access_token(
            data={"sub": user.email, "user_id": user.id, "purpose": "2fa_verify"},
            expires_delta=timedelta(minutes=5),
        )
        # Trả về temp_token
        return {"requires_2fa": True, "temp_token": temp_token}

    # Trả về token
    return _build_token_response(user)


# Profile & Password

# Get current user
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: User = Depends(utils.get_current_user)):
    # Trả về user hiện tại
    return current_user


# Update profile
@router.put("/update-profile", response_model=schemas.UserResponse)
def update_profile(
    data: schemas.UpdateProfileRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    # Kiểm tra họ và tên không được để trống
    if not data.full_name.strip():
        raise HTTPException(status_code=400, detail="Họ và tên không được để trống!")
    # Kiểm tra họ và tên phải có ít nhất 2 ký tự
    if len(data.full_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Họ và tên phải có ít nhất 2 ký tự!")

    # Cập nhật họ và tên
    current_user.full_name = data.full_name.strip()
    # Commit transaction
    db.commit()
    # Refresh user
    db.refresh(current_user)
    # Trả về user đã cập nhật
    return current_user


# Change password
@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    data: schemas.ChangePasswordRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    # Kiểm tra mật khẩu hiện tại không đúng
    if not utils.verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng!")

    # Cập nhật mật khẩu mới
    current_user.hashed_password = utils.get_password_hash(data.new_password)
    # Commit transaction
    db.commit()
    # Trả về message thành công
    return {"message": "Đổi mật khẩu thành công!"}


# 2FA — Two-Factor Authentication (TOTP)

# Get 2FA status
@router.get("/2fa/status")
def get_2fa_status(current_user: User = Depends(utils.get_current_user)):
    # Trả về status của 2FA
    return {"is_enabled": bool(current_user.is_2fa_enabled)}


# Setup 2FA
@router.post("/2fa/setup", response_model=schemas.TwoFactorSetupResponse)
def setup_2fa(
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Tạo TOTP secret mới + QR code. Chưa bật 2FA cho đến khi verify."""
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA đã được bật rồi!")

    # Tạo secret mới
    secret = pyotp.random_base32()
    # Cập nhật secret
    current_user.totp_secret = secret
    db.commit()

    # Tạo TOTP
    totp = pyotp.TOTP(secret)
    # Tạo URI TOTP
    otpauth_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Dental AI",
    )
    # Tạo QR code
    qr_code = _generate_qr_base64(otpauth_uri)
    # Trả về secret, QR code

    return {
        "secret": _format_secret(secret),
        "qr_code": qr_code,
    }


# Verify and enable 2FA
@router.post("/2fa/verify")
def verify_and_enable_2fa(
    data: schemas.TwoFactorCodeRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Xác thực mã TOTP lần đầu."""
    # Kiểm tra 2FA đã bật chưa
    if current_user.is_2fa_enabled:
        # Nếu 2FA đã bật, trả về lỗi
        raise HTTPException(status_code=400, detail="2FA đã được bật rồi!")
    # Kiểm tra secret có tồn tại chưa
    if not current_user.totp_secret:
        # Nếu secret không tồn tại, trả về lỗi
        raise HTTPException(status_code=400, detail="Chưa thiết lập 2FA. Hãy gọi /2fa/setup trước.")

    totp = pyotp.TOTP(current_user.totp_secret)
    # Kiểm tra mã TOTP có đúng không
    if not totp.verify(data.totp_code, valid_window=1):
        # Nếu mã TOTP không đúng, trả về lỗi
        raise HTTPException(status_code=400, detail="Mã xác thực không đúng hoặc đã hết hạn!")

    # Cập nhật status của 2FA
    current_user.is_2fa_enabled = True
    # Commit transaction
    db.commit()
    # Trả về message thành công
    return {"message": "Đã bật xác thực hai yếu tố thành công!"}


# Disable 2FA
@router.post("/2fa/disable")
def disable_2fa(
    data: schemas.TwoFactorCodeRequest,
    current_user: User = Depends(utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Tắt 2FA — yêu cầu mã TOTP hiện tại để xác nhận."""
    if not current_user.is_2fa_enabled:
        # Nếu 2FA chưa được bật, trả về lỗi
        raise HTTPException(status_code=400, detail="2FA chưa được bật!")
    # Kiểm tra secret có tồn tại chưa
    if not current_user.totp_secret:
        # Nếu secret không tồn tại, trả về lỗi
        raise HTTPException(status_code=400, detail="Chưa thiết lập 2FA. Hãy gọi /2fa/setup trước.")

    totp = pyotp.TOTP(current_user.totp_secret)
    # Kiểm tra mã TOTP có đúng không
    if not totp.verify(data.totp_code, valid_window=1):
        # Nếu mã TOTP không đúng, trả về lỗi
        raise HTTPException(status_code=400, detail="Mã xác thực không đúng!")

    # Cập nhật status của 2FA
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    db.commit()
    # Trả về message thành công
    return {"message": "Đã tắt xác thực hai yếu tố!"}


# Verify 2FA login
@router.post("/2fa/login-verify")
def verify_2fa_login(data: schemas.TwoFactorLoginRequest, db: Session = Depends(get_db)):
    """Bước 2 của login khi 2FA đang bật: xác thực mã TOTP + trả token thật."""
    try:
        # Giải mã token
        payload = jwt.decode(data.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        # Kiểm tra purpose có đúng không
        if payload.get("purpose") != "2fa_verify":
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        # Lấy email từ token
        email: str = payload.get("sub")
        # Nếu token hết hạn, trả về lỗi
    except JWTError:
        # Nếu token không hợp lệ, trả về lỗi
        raise HTTPException(status_code=401, detail="Token hết hạn. Vui lòng đăng nhập lại.")

    # Kiểm tra user có tồn tại chưa
    user = db.query(User).filter(User.email == email).first()
    # Nếu user không tồn tại hoặc 2FA chưa được bật hoặc secret không tồn tại, trả về lỗi
    if not user or not user.is_2fa_enabled or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Yêu cầu không hợp lệ")

    # Tạo TOTP
    totp = pyotp.TOTP(user.totp_secret)
    # Kiểm tra mã TOTP có đúng không
    if not totp.verify(data.totp_code, valid_window=1):
        # Nếu mã TOTP không đúng, trả về lỗi
        raise HTTPException(status_code=401, detail="Mã xác thực không đúng hoặc đã hết hạn!")

    # Trả về token
    return _build_token_response(user)
