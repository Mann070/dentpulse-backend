from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.prescription import Prescription
from app.models.patient_account import PatientAccount
from app.models.user import User
from app.models.planning import ConfirmedTreatmentPlan
from app.models.monitoring import Monitoring
from app.models.patient import Patient
from app.schemas.patient_schema import PrescriptionCreateSchema
from app.routes.auth import get_current_user
from app.routes.patient_auth import get_current_patient

router = APIRouter(prefix="/recovery", tags=["Recovery & Prescriptions"])


@router.get("/timeline")
async def get_recovery_timeline(
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    """Returns treatment journey timeline for the logged-in patient."""

    # Try to find linked doctor-managed patient by first name
    first_name = current_patient.full_name.split()[0]
    pat_result = await db.execute(
        select(Patient).filter(Patient.full_name.ilike(f"%{first_name}%"))
    )
    doctor_patient = pat_result.scalars().first()

    timeline_events = []

    if doctor_patient:
        # Confirmed treatment plans
        plan_result = await db.execute(
            select(ConfirmedTreatmentPlan)
            .filter(ConfirmedTreatmentPlan.patient_id == doctor_patient.id)
            .order_by(ConfirmedTreatmentPlan.created_at.asc())
        )
        plans = plan_result.scalars().all()
        for plan in plans:
            timeline_events.append(
                {
                    "type": "plan",
                    "title": "Implant Planning Completed",
                    "detail": f"{plan.implant_type} — {plan.implant_diameter}mm × {plan.implant_length}mm",
                    "date": plan.created_at.strftime("%d %b %Y") if plan.created_at else "",
                    "status": "completed",
                    "icon": "check",
                }
            )

        # Monitoring history
        mon_result = await db.execute(
            select(Monitoring)
            .filter(Monitoring.patient_id == doctor_patient.id)
            .order_by(Monitoring.created_at.asc())
        )
        monitorings = mon_result.scalars().all()
        for i, mon in enumerate(monitorings):
            week = (i + 1) * 2
            svm = getattr(mon, "svm_prediction", None) or "Low Risk"
            timeline_events.append(
                {
                    "type": "monitoring",
                    "title": f"Week {week} Monitoring",
                    "detail": f"Risk: {svm} | ISQ: {mon.isq_value or '—'}",
                    "date": mon.created_at.strftime("%d %b %Y") if mon.created_at else "",
                    "status": "completed",
                    "icon": "activity",
                }
            )

    # Prescriptions
    rx_result = await db.execute(
        select(Prescription)
        .filter(Prescription.patient_account_id == current_patient.id)
        .order_by(Prescription.created_at.asc())
    )
    rxs = rx_result.scalars().all()
    for rx in rxs:
        timeline_events.append(
            {
                "type": "prescription",
                "title": "Prescription Issued",
                "detail": f"{rx.medicine_name} — {rx.dosage}",
                "date": rx.created_at.strftime("%d %b %Y") if rx.created_at else "",
                "status": "completed",
                "icon": "pill",
            }
        )

    # Sort chronologically and append pending follow-up placeholder
    timeline_events.sort(key=lambda x: x.get("date", ""))
    timeline_events.append(
        {
            "type": "followup",
            "title": "Next Follow-up",
            "detail": "Scheduled with your doctor",
            "date": "",
            "status": "pending",
            "icon": "clock",
        }
    )

    return timeline_events


@router.get("/status")
async def get_recovery_status(
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    """Returns simplified recovery metrics for the patient dashboard."""

    first_name = current_patient.full_name.split()[0]
    pat_result = await db.execute(
        select(Patient).filter(Patient.full_name.ilike(f"%{first_name}%"))
    )
    doctor_patient = pat_result.scalars().first()

    recovery_score = 75
    healing_status = "Healing Progressing"
    next_followup = "Consult your doctor"
    doctor_notes = "Follow post-operative care instructions."
    risk_level = "Low"

    if doctor_patient:
        # Latest monitoring record
        mon_result = await db.execute(
            select(Monitoring)
            .filter(Monitoring.patient_id == doctor_patient.id)
            .order_by(Monitoring.created_at.desc())
        )
        latest_mon = mon_result.scalars().first()

        if latest_mon:
            isq = latest_mon.isq_value or 65
            recovery_score = min(99, int((isq / 85) * 100))
            svm = getattr(latest_mon, "svm_prediction", "Low Risk") or "Low Risk"
            if "High" in svm or "Critical" in svm:
                healing_status = "Needs Attention"
                risk_level = "High"
            elif "Moderate" in svm:
                healing_status = "Monitoring Closely"
                risk_level = "Moderate"
            else:
                healing_status = "Healing Stable"
                risk_level = "Low"

        # Latest confirmed plan for doctor notes
        plan_result = await db.execute(
            select(ConfirmedTreatmentPlan)
            .filter(ConfirmedTreatmentPlan.patient_id == doctor_patient.id)
            .order_by(ConfirmedTreatmentPlan.created_at.desc())
        )
        latest_plan = plan_result.scalars().first()
        if latest_plan:
            doctor_notes = (
                f"Implant: {latest_plan.implant_type}. "
                f"Risk Level: {latest_plan.risk_level or 'Low'}. "
                "Follow post-op care."
            )

    return {
        "recovery_score": recovery_score,
        "healing_status": healing_status,
        "next_followup": next_followup,
        "doctor_notes": doctor_notes,
        "risk_level": risk_level,
    }


@router.get("/prescriptions")
async def get_my_prescriptions(
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    result = await db.execute(
        select(Prescription)
        .filter(Prescription.patient_account_id == current_patient.id)
        .order_by(Prescription.created_at.desc())
    )
    prescriptions = result.scalars().all()

    enriched = []
    for rx in prescriptions:
        doc_result = await db.execute(select(User).filter(User.id == rx.doctor_id))
        doctor = doc_result.scalars().first()
        enriched.append(
            {
                "id": rx.id,
                "medicine_name": rx.medicine_name,
                "dosage": rx.dosage,
                "instructions": rx.instructions,
                "duration": rx.duration,
                "doctor_name": doctor.full_name if doctor else "Your Doctor",
                "created_at": rx.created_at.strftime("%d %b %Y") if rx.created_at else "",
            }
        )
    return enriched


@router.post("/prescriptions")
async def add_prescription(
    payload: PrescriptionCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_user),
):
    # Verify target patient account exists
    pat_result = await db.execute(
        select(PatientAccount).filter(PatientAccount.id == payload.patient_account_id)
    )
    patient = pat_result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient account not found")

    rx = Prescription(
        patient_account_id=payload.patient_account_id,
        doctor_id=current_doctor.id,
        medicine_name=payload.medicine_name,
        dosage=payload.dosage,
        instructions=payload.instructions,
        duration=payload.duration,
    )
    db.add(rx)
    await db.commit()
    await db.refresh(rx)
    return {"message": "Prescription added", "id": rx.id}


@router.get("/patients-list")
async def get_registered_patients(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_user),
):
    """Doctor gets list of self-registered, verified patients to prescribe to."""
    result = await db.execute(
        select(PatientAccount)
        .filter(PatientAccount.is_verified == True)
        .order_by(PatientAccount.created_at.desc())
    )
    patients = result.scalars().all()
    return [
        {
            "id": p.id,
            "full_name": p.full_name,
            "age": p.age,
            "gender": p.gender,
            "email": p.email,
            "phone_number": p.phone_number,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in patients
    ]
