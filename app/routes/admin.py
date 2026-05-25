from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.user import User
from app.models.login_history import LoginHistory
from app.schemas.user_schema import DoctorApprovalResponse, LoginHistoryResponse
from app.routes.auth import get_current_user
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin Control Panel"])

# Role guard dependency
async def check_admin_role(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin credentials required to access this portal."
        )
    return current_user


@router.get("/pending-doctors", response_model=List[DoctorApprovalResponse])
async def get_pending_doctors(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    result = await db.execute(
        select(User).filter(User.role == "doctor", User.approval_status == "pending").order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.get("/approved-doctors", response_model=List[DoctorApprovalResponse])
async def get_approved_doctors(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    result = await db.execute(
        select(User).filter(User.role == "doctor", User.approval_status == "approved").order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.post("/approve-doctor/{id}")
async def approve_doctor(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    result = await db.execute(select(User).filter(User.id == id, User.role == "doctor"))
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor account not found")
        
    doctor.is_approved = True
    doctor.approval_status = "approved"
    
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return {"message": f"Doctor {doctor.full_name} has been successfully approved.", "status": "approved"}


@router.post("/reject-doctor/{id}")
async def reject_doctor(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    result = await db.execute(select(User).filter(User.id == id, User.role == "doctor"))
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor account not found")
        
    doctor.is_approved = False
    doctor.approval_status = "rejected"
    
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return {"message": f"Doctor {doctor.full_name} has been successfully rejected.", "status": "rejected"}


@router.get("/login-history", response_model=List[LoginHistoryResponse])
async def get_login_history(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    # Join LoginHistory with User to get user_name and email
    query = (
        select(
            LoginHistory.id,
            User.full_name.label("user_name"),
            User.email,
            LoginHistory.login_time,
            LoginHistory.device_info,
            LoginHistory.login_status
        )
        .join(User, LoginHistory.user_id == User.id)
        .order_by(LoginHistory.login_time.desc())
        .limit(200)
    )
    result = await db.execute(query)
    
    histories = []
    for row in result.all():
        histories.append({
            "id": row.id,
            "user_name": row.user_name,
            "email": row.email,
            "login_time": row.login_time,
            "device_info": row.device_info,
            "login_status": row.login_status
        })
    return histories
