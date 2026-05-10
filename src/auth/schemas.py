
from pydantic import BaseModel, model_validator
from typing import Optional


# Đăng ký
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
        return self

# Đăng nhập
class UserLogin(BaseModel):
    email: str
    password: str

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    full_name: str
    email: str

# Thông tin user
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_2fa_enabled: bool = False

    # Cấu hình
    class Config:
        from_attributes = True


# Cập nhật thông tin người dùng
class UpdateProfileRequest(BaseModel):
    full_name: str

# Đổi mật khẩu
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
        return self


# 2FA

# Thiết lập 2FA
class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str

# Mã OTP
class TwoFactorCodeRequest(BaseModel):
    totp_code: str

# Xác thực đăng nhập 2FA
class TwoFactorLoginRequest(BaseModel):
    temp_token: str
    totp_code: str
