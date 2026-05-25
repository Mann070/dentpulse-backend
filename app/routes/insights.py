from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.insights import Insights
from app.schemas.insight_schema import InsightResponse
from datetime import datetime

router = APIRouter(prefix="/insights", tags=["Insights"])

@router.get("/{patient_id}", response_model=InsightResponse)
async def get_patient_insights(patient_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Insights)
        .filter(Insights.patient_id == patient_id)
        .order_by(Insights.generated_at.desc())
    )
    insight = result.scalars().first()
    
    if not insight:
        # Return a safe default if no monitoring data exists yet
        return {
            "id": 0,
            "patient_id": patient_id,
            "complication_risk": "Pending",
            "ai_confidence": "N/A",
            "recommendation": "No monitoring data logged yet.",
            "alert_level": "Low",
            "generated_at": datetime.now()
        }
        
    return insight
