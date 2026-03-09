from pydantic import BaseModel, model_validator

# Dùng cho Đăng ký (Có confirm_password)
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    confirm_password: str

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserCreate':
        if self.password != self.confirm_password:
            raise ValueError('Mật khẩu xác nhận không khớp!')
        return self

# Dùng cho Đăng nhập
class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    full_name: str
    email: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True