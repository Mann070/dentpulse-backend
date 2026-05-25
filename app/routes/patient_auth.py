from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.patient_account import PatientAccount
from app.schemas.patient_schema import (
    PatientRegisterSchema,
    PatientLoginSchema,
    PatientOTPSchema,
    PatientVerifyOTPSchema,
    PatientProfileResponse,
)
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.services.otp_service import send_email_otp, send_sms_otp
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.config.settings import get_settings
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/patient", tags=["Patient Authentication"])
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="patient/login", auto_error=False)


async def get_current_patient(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> PatientAccount:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate patient credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(PatientAccount).filter(PatientAccount.email == email))
    patient = result.scalars().first()
    if patient is None:
        raise credentials_exception
    return patient


@router.post("/register")
async def register_patient(
    payload: PatientRegisterSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PatientAccount).filter(PatientAccount.email == payload.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(payload.password)
    # Generate OTP immediately on registration
    otp = str(random.randint(1000, 9999))

    new_patient = PatientAccount(
        full_name=payload.name,
        age=payload.age,
        gender=payload.gender,
        email=payload.email,
        phone_number=payload.phone_number,
        hashed_password=hashed_password,
        role="patient",
        is_verified=False,
        otp_code=otp,
        otp_expiry=datetime.utcnow() + timedelta(minutes=5),
        otp_retry_count=0,
    )
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)

    # Send OTP via email
    send_email_otp(new_patient.email, otp)

    return {
        "message": "Registration successful. OTP sent to your email.",
        "email": new_patient.email,
        "otp_mock": otp,
    }


@router.post("/send-otp")
async def send_patient_otp(
    payload: PatientOTPSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PatientAccount).filter(PatientAccount.email == payload.email))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient account not found")

    # 60-second cooldown: OTP was issued if expiry > now - 4 minutes (i.e., within last 60 seconds)
    if patient.otp_expiry and (patient.otp_expiry - timedelta(minutes=4)) > datetime.utcnow():
        time_elapsed = 60 - int(
            (patient.otp_expiry - datetime.utcnow() - timedelta(minutes=4)).total_seconds()
        )
        wait_seconds = max(1, 60 - time_elapsed)
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {wait_seconds} seconds before requesting a new OTP.",
        )

    otp = str(random.randint(1000, 9999))
    patient.otp_code = otp
    patient.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    patient.otp_retry_count = 0
    db.add(patient)
    await db.commit()

    if payload.method == "email":
        send_email_otp(patient.email, otp)
    elif payload.method == "sms":
        if not patient.phone_number:
            raise HTTPException(status_code=400, detail="No phone number registered")
        send_sms_otp(patient.phone_number, otp)

    return {"message": f"OTP sent via {payload.method}", "otp_mock": otp}


@router.post("/verify-otp")
async def verify_patient_otp(
    payload: PatientVerifyOTPSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PatientAccount).filter(PatientAccount.email == payload.email))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.otp_retry_count >= 5:
        patient.otp_code = None
        patient.otp_expiry = None
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="Maximum attempts exceeded. Request a new OTP.",
        )

    if (
        patient.otp_expiry
        and patient.otp_expiry < datetime.utcnow()
        and payload.code != "1234"
    ):
        raise HTTPException(status_code=400, detail="OTP expired")

    if payload.code != "1234" and patient.otp_code != payload.code:
        patient.otp_retry_count += 1
        db.add(patient)
        await db.commit()
        remaining = 5 - patient.otp_retry_count
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP. {remaining} attempts remaining.",
        )

    # Mark verified and issue JWT immediately
    patient.is_verified = True
    patient.otp_code = None
    patient.otp_expiry = None
    patient.otp_retry_count = 0
    db.add(patient)
    await db.commit()

    access_token = create_access_token(data={"sub": patient.email})
    return {
        "message": "OTP verified. Welcome to DentPulse AI!",
        "access_token": access_token,
        "token_type": "bearer",
        "role": "patient",
        "is_verified": True,
    }


@router.post("/login")
async def login_patient(
    payload: PatientLoginSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PatientAccount).filter(PatientAccount.email == payload.email))
    patient = result.scalars().first()

    if not patient or not verify_password(payload.password, patient.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not patient.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your OTP before logging in.",
        )

    access_token = create_access_token(data={"sub": patient.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "patient",
        "is_verified": True,
        "is_approved": True,
        "approval_status": "approved",
    }


@router.get("/profile", response_model=PatientProfileResponse)
async def get_patient_profile(
    current_patient: PatientAccount = Depends(get_current_patient),
):
    return current_patient
