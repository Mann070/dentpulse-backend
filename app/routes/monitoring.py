from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.services.monitoring_engine import MonitoringEngine
from app.models.monitoring import Monitoring
from app.models.insights import Insights
from app.models.patient import Patient
from app.schemas.monitoring_schema import MonitoringCreate, MonitoringResponse
from app.routes.auth import get_current_user
from app.models.user import User
from typing import List, Optional, Any, Dict
import json

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.post("/log")
async def log_monitoring(
    data: MonitoringCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    uploaded_scan = data.uploaded_scan or "xray_normal.png"

    # ── CNN analysis ──────────────────────────────────────────────────────
    cnn_res = MonitoringEngine.run_cnn_analysis(
        uploaded_scan_name=uploaded_scan,
        isq_score=data.isq_score,
        bone_level=data.bone_loss,
    )

    # ── SVM prediction ────────────────────────────────────────────────────
    svm_res = MonitoringEngine.run_svm_prediction(
        isq_score=data.isq_score,
        bone_level=data.bone_loss,
        mobility=data.mobility,
        pain_level=data.pain_level,
        swelling=data.swelling,
        bleeding=data.bleeding,
        cnn_result=cnn_res,
    )

    # ── Persist monitoring record ─────────────────────────────────────────
    db_monitoring = Monitoring(
        patient_id=data.patient_id,
        doctor_id=current_user.id if current_user else data.doctor_id,
        bone_loss=data.bone_loss,
        isq_score=data.isq_score,
        pain_level=data.pain_level,
        swelling=data.swelling,
        bleeding=data.bleeding,
        mobility=data.mobility,
        uploaded_scan=uploaded_scan,
        cnn_result=json.dumps(cnn_res),
        svm_prediction=json.dumps(svm_res),
    )
    db.add(db_monitoring)

    # ── Persist insights (backward-compat) ────────────────────────────────
    db_insight = Insights(
        patient_id=data.patient_id,
        complication_risk=f"{svm_res['complication_probability']}%",
        ai_confidence=f"{cnn_res['confidence']}%",
        recommendation=svm_res["alerts"][0] if svm_res["alerts"] else "Stable: healing on track",
        alert_level=svm_res["risk_level"].split()[0],   # "Low" / "Moderate" / "High"
    )
    db.add(db_insight)

    # ── Update patient risk level ─────────────────────────────────────────
    result = await db.execute(select(Patient).filter(Patient.id == data.patient_id))
    patient = result.scalars().first()
    if patient:
        patient.risk_level = svm_res["risk_level"].split()[0]
        db.add(patient)

    await db.commit()
    await db.refresh(db_monitoring)

    # ── Return enriched payload ───────────────────────────────────────────
    return {
        "id": db_monitoring.id,
        "patient_id": db_monitoring.patient_id,
        "monitoring_date": db_monitoring.monitoring_date,
        "isq_score": db_monitoring.isq_score,
        "bone_loss": db_monitoring.bone_loss,
        "mobility": db_monitoring.mobility,
        "pain_level": db_monitoring.pain_level,
        "swelling": db_monitoring.swelling,
        "bleeding": db_monitoring.bleeding,
        "uploaded_scan": db_monitoring.uploaded_scan,
        "cnn": cnn_res,
        "svm": svm_res,
    }


@router.get("/{patient_id}")
async def get_history(patient_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Monitoring)
        .filter(Monitoring.patient_id == patient_id)
        .order_by(Monitoring.monitoring_date.asc())
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "monitoring_date": r.monitoring_date,
            "isq_score": r.isq_score,
            "bone_loss": r.bone_loss,
            "mobility": r.mobility,
            "cnn_result": json.loads(r.cnn_result) if r.cnn_result else None,
            "svm_prediction": json.loads(r.svm_prediction) if r.svm_prediction else None,
        }
        for r in records
    ]
