from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.appointment import Appointment
from app.models.patient_account import PatientAccount
from app.models.user import User
from app.schemas.patient_schema import AppointmentBookSchema, AppointmentRescheduleSchema
from app.routes.auth import get_current_user
from app.routes.patient_auth import get_current_patient
import random
import string

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def generate_meeting_link() -> str:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"https://meet.dentpulse.ai/room/{code}"


@router.get("/approved-doctors")
async def get_approved_doctors(db: AsyncSession = Depends(get_db)):
    """Public endpoint — list all approved doctors available for patient booking."""
    result = await db.execute(
        select(User).filter(
            User.role == "doctor",
            User.approval_status == "approved",
            User.is_approved == True,
        )
    )
    doctors = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.full_name,
            "specialization": d.specialization or "Prosthodontist",
            "clinic_name": d.clinic_name or "DentPulse Clinic",
            "phone_number": d.phone_number,
            "email": d.email,
            "availability": "Mon–Sat, 9AM–6PM",
        }
        for d in doctors
    ]


@router.post("/book")
async def book_appointment(
    payload: AppointmentBookSchema,
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    # Verify doctor exists and is approved
    result = await db.execute(
        select(User).filter(
            User.id == payload.doctor_id,
            User.role == "doctor",
            User.is_approved == True,
        )
    )
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or not approved")

    meeting_link = generate_meeting_link() if payload.consultation_type == "virtual" else None

    appointment = Appointment(
        patient_account_id=current_patient.id,
        doctor_id=payload.doctor_id,
        date=payload.date,
        time=payload.time,
        consultation_type=payload.consultation_type,
        status="pending",
        meeting_link=meeting_link,
        patient_notes=payload.patient_notes,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    return {
        "id": appointment.id,
        "message": "Appointment booked successfully",
        "status": "pending",
        "meeting_link": meeting_link,
        "doctor_name": doctor.full_name,
        "date": payload.date,
        "time": payload.time,
        "consultation_type": payload.consultation_type,
    }


@router.get("/my")
async def get_my_appointments(
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    result = await db.execute(
        select(Appointment)
        .filter(Appointment.patient_account_id == current_patient.id)
        .order_by(Appointment.created_at.desc())
    )
    appointments = result.scalars().all()

    enriched = []
    for appt in appointments:
        doc_result = await db.execute(select(User).filter(User.id == appt.doctor_id))
        doctor = doc_result.scalars().first()
        enriched.append(
            {
                "id": appt.id,
                "doctor_name": doctor.full_name if doctor else "Unknown",
                "doctor_specialization": doctor.specialization if doctor else "Prosthodontist",
                "clinic_name": doctor.clinic_name if doctor else "DentPulse Clinic",
                "date": appt.date,
                "time": appt.time,
                "consultation_type": appt.consultation_type,
                "status": appt.status,
                "meeting_link": appt.meeting_link,
                "patient_notes": appt.patient_notes,
                "doctor_notes": appt.doctor_notes,
                "created_at": appt.created_at.isoformat() if appt.created_at else None,
            }
        )
    return enriched


@router.get("/doctor")
async def get_doctor_appointments(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment)
        .filter(Appointment.doctor_id == current_doctor.id)
        .order_by(Appointment.created_at.desc())
    )
    appointments = result.scalars().all()

    enriched = []
    for appt in appointments:
        pat_result = await db.execute(
            select(PatientAccount).filter(PatientAccount.id == appt.patient_account_id)
        )
        patient = pat_result.scalars().first()
        enriched.append(
            {
                "id": appt.id,
                "patient_name": patient.full_name if patient else "Unknown",
                "patient_email": patient.email if patient else "",
                "patient_age": patient.age if patient else None,
                "date": appt.date,
                "time": appt.time,
                "consultation_type": appt.consultation_type,
                "status": appt.status,
                "meeting_link": appt.meeting_link,
                "patient_notes": appt.patient_notes,
                "doctor_notes": appt.doctor_notes,
                "created_at": appt.created_at.isoformat() if appt.created_at else None,
            }
        )
    return enriched


@router.post("/{appointment_id}/accept")
async def accept_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.doctor_id == current_doctor.id,
        )
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "accepted"
    db.add(appt)
    await db.commit()
    return {"message": "Appointment accepted", "status": "accepted"}


@router.post("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: int,
    payload: AppointmentRescheduleSchema,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.doctor_id == current_doctor.id,
        )
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.date = payload.new_date
    appt.time = payload.new_time
    appt.status = "rescheduled"
    db.add(appt)
    await db.commit()
    return {
        "message": "Appointment rescheduled",
        "new_date": payload.new_date,
        "new_time": payload.new_time,
    }


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.doctor_id == current_doctor.id,
        )
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "completed"
    db.add(appt)
    await db.commit()
    return {"message": "Appointment marked complete"}


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    result = await db.execute(
        select(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.patient_account_id == current_patient.id,
        )
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "cancelled"
    db.add(appt)
    await db.commit()
    return {"message": "Appointment cancelled"}
