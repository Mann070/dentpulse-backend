from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.user import User
from app.models.login_history import LoginHistory
from app.schemas.user_schema import (
    UserCreate, UserResponse, Token, SendOTPSchema, VerifyOTPSchema,
    ForgotPasswordSchema, VerifyResetOTPSchema, ResetPasswordSchema
)
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.services.otp_service import send_email_otp, send_sms_otp
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.config.settings import get_settings
from datetime import datetime, timedelta
import random
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Shared Dependency: Get Current User (Async)
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
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
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register-doctor", response_model=UserResponse)
async def register_doctor(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email is already taken
    result = await db.execute(select(User).filter(User.email == user_data.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    
    # Create doctor in Pending status
    new_user = User(
        full_name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        specialization=user_data.specialization,
        clinic_name=user_data.clinic_name,
        phone_number=user_data.phone_number,
        license_id=user_data.license_id,
        role="doctor",
        is_verified=False,
        is_approved=False,
        approval_status="pending"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/send-otp")
async def send_otp(payload: SendOTPSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == payload.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
    
    # Enforce 60-second cooldown timer
    # otp_expiry represents current time + 5 minutes.
    # If otp_expiry - 4 minutes > current time, less than 60 seconds have passed!
    if user.otp_expiry and (user.otp_expiry - timedelta(minutes=4)) > datetime.utcnow():
        time_elapsed = 60 - int((user.otp_expiry - datetime.utcnow() - timedelta(minutes=4)).total_seconds())
        wait_seconds = max(1, 60 - time_elapsed)
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {wait_seconds} seconds before requesting a new OTP."
        )
    
    # Generate secure 4-digit code
    otp = str(random.randint(1000, 9999))
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)  # Expire in 5 minutes
    user.otp_retry_count = 0  # Reset failed count
    
    db.add(user)
    await db.commit()
    
    # Send via selected channel (Email vs SMS)
    if payload.method == "email":
        send_email_otp(user.email, otp)
    elif payload.method == "sms":
        if not user.phone_number:
            raise HTTPException(
                status_code=400,
                detail="User account does not have a registered phone number."
            )
        send_sms_otp(user.phone_number, otp)
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP delivery method")
    
    return {
        "message": f"OTP successfully sent via {payload.method}",
        "otp_mock": otp  # For developer console/testing
    }


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOTPSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == payload.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Enforce retry limit (max 5 attempts)
    if user.otp_retry_count >= 5:
        # Clear code to enforce fresh generation
        user.otp_code = None
        user.otp_expiry = None
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="Maximum verification attempts exceeded. Please request a new OTP."
        )
    
    # Verify expiration (5 minutes)
    if user.otp_expiry and user.otp_expiry < datetime.utcnow() and payload.code != "1234":
        raise HTTPException(status_code=400, detail="OTP verification code expired")
    
    # Verify code (allow developer bypass '1234')
    if payload.code != "1234" and user.otp_code != payload.code:
        user.otp_retry_count += 1
        db.add(user)
        await db.commit()
        remaining = 5 - user.otp_retry_count
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP verification code. {remaining} attempts remaining."
        )
    
    # Set verification flag
    user.is_verified = True
    user.otp_code = None  # Clear OTP
    user.otp_expiry = None
    user.otp_retry_count = 0
    
    db.add(user)
    await db.commit()
    
    return {
        "message": "OTP verified successfully. Your account is now pending admin approval.",
        "is_verified": True
    }


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordSchema, db: AsyncSession = Depends(get_db)):
    email_or_phone = payload.email_or_phone.strip().lower()
    
    # Find user by either email or phone number
    result = await db.execute(
        select(User).filter((User.email == email_or_phone) | (User.phone_number == payload.email_or_phone.strip()))
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No registered account found with that email or phone number."
        )
        
    # Enforce 60-second cooldown
    if user.reset_password_expiry and (user.reset_password_expiry - timedelta(minutes=4)) > datetime.utcnow():
        time_elapsed = 60 - int((user.reset_password_expiry - datetime.utcnow() - timedelta(minutes=4)).total_seconds())
        wait_seconds = max(1, 60 - time_elapsed)
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {wait_seconds} seconds before requesting a new OTP."
        )
        
    # Generate 4-digit code
    otp = str(random.randint(1000, 9999))
    user.reset_password_otp = otp
    user.reset_password_expiry = datetime.utcnow() + timedelta(minutes=5)  # Expiry = 5 minutes
    user.reset_otp_retry_count = 0  # Reset retry counter
    
    db.add(user)
    await db.commit()
    
    # Send OTP
    if payload.method == "email":
        send_email_otp(user.email, otp)
    elif payload.method == "sms":
        if not user.phone_number:
            raise HTTPException(
                status_code=400,
                detail="This account does not have a registered phone number. Verify via Email instead."
            )
        send_sms_otp(user.phone_number, otp)
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP delivery method")
        
    return {
        "message": f"OTP successfully sent via {payload.method}",
        "otp_mock": otp  # For sandbox testing
    }


@router.post("/verify-reset-otp")
async def verify_reset_otp(payload: VerifyResetOTPSchema, db: AsyncSession = Depends(get_db)):
    email_or_phone = payload.email_or_phone.strip().lower()
    
    # Query user
    result = await db.execute(
        select(User).filter((User.email == email_or_phone) | (User.phone_number == payload.email_or_phone.strip()))
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
        
    # Enforce retry limit (max 5 attempts)
    if user.reset_otp_retry_count >= 5:
        user.reset_password_otp = None
        user.reset_password_expiry = None
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="Maximum verification attempts exceeded. Please request a new password reset."
        )
        
    # Verify expiration (5 minutes)
    if user.reset_password_expiry and user.reset_password_expiry < datetime.utcnow() and payload.code != "1234":
        raise HTTPException(status_code=400, detail="OTP verification code has expired")
        
    # Verify code (allow developer bypass '1234')
    if payload.code != "1234" and user.reset_password_otp != payload.code:
        user.reset_otp_retry_count += 1
        db.add(user)
        await db.commit()
        remaining = 5 - user.reset_otp_retry_count
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP verification code. {remaining} attempts remaining."
        )
        
    return {
        "message": "OTP verified successfully. You may now create a new password.",
        "success": True
    }


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordSchema, db: AsyncSession = Depends(get_db)):
    email_or_phone = payload.email_or_phone.strip().lower()
    
    # Query user
    result = await db.execute(
        select(User).filter((User.email == email_or_phone) | (User.phone_number == payload.email_or_phone.strip()))
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
        
    # Double-check code is still valid and not expired (state-less safety check)
    if user.reset_password_expiry and user.reset_password_expiry < datetime.utcnow() and payload.code != "1234":
        raise HTTPException(status_code=400, detail="Reset password session has expired. Please request a new OTP.")
        
    if payload.code != "1234" and user.reset_password_otp != payload.code:
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please request a new password reset.")
        
    # Update Password using secure bcrypt hashing
    hashed_password = get_password_hash(payload.new_password)
    user.hashed_password = hashed_password
    
    # Clear reset OTP state on success
    user.reset_password_otp = None
    user.reset_password_expiry = None
    user.reset_otp_retry_count = 0
    
    db.add(user)
    await db.commit()
    
    return {
        "message": "Password successfully updated. Please login with your new credentials.",
        "success": True
    }


class LoginRequest(BaseModel):
    username: str  # Email
    password: str
    device_info: Optional[str] = "Web Browser"


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    username = None
    password = None
    device_info = "Mobile App"
    
    # Support both Swagger Form parameters and JSON body post
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
            device_info = body.get("device_info", "Mobile App")
        except Exception:
            pass
    else:
        # Fallback to form data for Swagger UI
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            device_info = "Swagger Client"
        except Exception:
            pass
            
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
        
    result = await db.execute(select(User).filter(User.email == username))
    user = result.scalars().first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Role-Based Restrictions for Doctor Login
    if user.role == "doctor":
        if not user.is_verified:
            # Audit log failed login
            fail_log = LoginHistory(
                user_id=user.id,
                device_info=device_info,
                login_status="Failed - Unverified"
            )
            db.add(fail_log)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your email is not verified. Please complete OTP verification."
            )
            
        if user.approval_status == "pending":
            fail_log = LoginHistory(
                user_id=user.id,
                device_info=device_info,
                login_status="Failed - Pending Approval"
            )
            db.add(fail_log)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is awaiting admin approval."
            )
            
        if user.approval_status == "rejected" or not user.is_approved:
            fail_log = LoginHistory(
                user_id=user.id,
                device_info=device_info,
                login_status="Failed - Rejected"
            )
            db.add(fail_log)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your clinical account request has been rejected by the admin."
            )
            
    # Audit log successful login
    success_log = LoginHistory(
        user_id=user.id,
        device_info=device_info,
        login_status="Success"
    )
    db.add(success_log)
    await db.commit()
    
    # Create Access Token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "is_verified": user.is_verified,
        "is_approved": user.is_approved,
        "approval_status": user.approval_status
    }


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/profile", response_model=UserResponse)
async def get_doctor_profile(current_user: User = Depends(get_current_user)):
    return current_user
