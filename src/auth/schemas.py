# src/auth/schemas.py
# Schemas for authentication endpoints
from pydantic import BaseModel, model_validator
from typing import Optional


# Auth — Register / Login

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    confirm_password: str

    # Kiểm tra mật khẩu xác nhận có khớp không
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserCreate':
        if self.password != self.confirm_password:
            raise ValueError('Mật khẩu xác nhận không khớp!')
        # Trả về user create
        return self

# User Login
class UserLogin(BaseModel):
    email: str
    password: str

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    full_name: str
    email: str

# User Response
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_2fa_enabled: bool = False

    # Config
    class Config:
        from_attributes = True


# Profile / Password

# Update Profile Request
class UpdateProfileRequest(BaseModel):
    full_name: str

# Change Password Request
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

    # Kiểm tra mật khẩu xác nhận có khớp không
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'ChangePasswordRequest':
        if self.new_password != self.confirm_new_password:
            raise ValueError('Mật khẩu xác nhận không khớp!')
        if len(self.new_password) < 6:
            raise ValueError('Mật khẩu mới phải có ít nhất 6 ký tự!')
        # Trả về change password request
        return self


# 2FA (Two-Factor Authentication)

# Two Factor Setup Response
class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str

# Two Factor Code Request
class TwoFactorCodeRequest(BaseModel):
    totp_code: str

# Two Factor Login Request
class TwoFactorLoginRequest(BaseModel):
    temp_token: str
    totp_code: str
