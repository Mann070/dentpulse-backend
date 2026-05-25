from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    specialization: Optional[str] = None
    clinic_name: Optional[str] = None
    phone_number: Optional[str] = None
    license_id: Optional[str] = None
    role: str = "doctor"
    is_verified: bool = False
    is_approved: bool = False
    approval_status: str = "pending"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: Any

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    is_verified: bool
    is_approved: bool
    approval_status: str

class TokenData(BaseModel):
    email: Optional[str] = None

class SendOTPSchema(BaseModel):
    email: EmailStr
    method: str  # "email" or "sms"

class VerifyOTPSchema(BaseModel):
    email: EmailStr
    code: str

class DoctorApprovalResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: Optional[str]
    specialization: Optional[str]
    clinic_name: Optional[str]
    license_id: Optional[str]
    approval_status: str
    is_verified: bool
    is_approved: bool
    created_at: Any

    class Config:
        from_attributes = True

class LoginHistoryResponse(BaseModel):
    id: int
    user_name: str
    email: str
    login_time: datetime
    device_info: Optional[str]
    login_status: str

    class Config:
        from_attributes = True


class ForgotPasswordSchema(BaseModel):
    email_or_phone: str
    method: str  # "email" or "sms"


class VerifyResetOTPSchema(BaseModel):
    email_or_phone: str
    code: str


class ResetPasswordSchema(BaseModel):
    email_or_phone: str
    code: str
    new_password: str


