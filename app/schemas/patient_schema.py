from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import date, datetime


# ─── Existing: Doctor-managed patient schemas ──────────────────────────────────

class PatientBase(BaseModel):
    patient_id: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    implant_site: Optional[str] = None
    implant_type: Optional[str] = None
    surgery_date: Optional[date] = None
    risk_level: Optional[str] = "Low"


class PatientCreate(PatientBase):
    doctor_id: Optional[int] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    risk_level: Optional[str] = None


class PatientResponse(PatientBase):
    id: int
    doctor_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── New: Self-registered PatientAccount schemas ───────────────────────────────

class PatientRegisterSchema(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    email: EmailStr
    phone_number: Optional[str] = None
    password: str


class PatientLoginSchema(BaseModel):
    email: EmailStr
    password: str


class PatientOTPSchema(BaseModel):
    email: EmailStr
    method: str  # email or sms


class PatientVerifyOTPSchema(BaseModel):
    email: EmailStr
    code: str


class PatientProfileResponse(BaseModel):
    id: int
    full_name: str
    age: Optional[int]
    gender: Optional[str]
    email: str
    phone_number: Optional[str]
    role: str
    is_verified: bool
    created_at: Any

    class Config:
        from_attributes = True


# ─── New: Appointment schemas ──────────────────────────────────────────────────

class AppointmentBookSchema(BaseModel):
    doctor_id: int
    date: str
    time: str
    consultation_type: str  # physical / virtual
    patient_notes: Optional[str] = None


class AppointmentRescheduleSchema(BaseModel):
    new_date: str
    new_time: str


# ─── New: Prescription schemas ─────────────────────────────────────────────────

class PrescriptionCreateSchema(BaseModel):
    patient_account_id: int
    medicine_name: str
    dosage: str
    instructions: Optional[str] = None
    duration: Optional[str] = None


# ─── New: Chatbot schema ───────────────────────────────────────────────────────

class ChatbotMessageSchema(BaseModel):
    message: str


# ─── New: Recovery update schema ──────────────────────────────────────────────

class RecoveryUpdateSchema(BaseModel):
    patient_account_id: int
    recovery_score: Optional[int] = None
    healing_status: Optional[str] = None
    next_followup_date: Optional[str] = None
    doctor_notes: Optional[str] = None
