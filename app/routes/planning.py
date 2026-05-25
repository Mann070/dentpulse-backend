from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.schemas.planning_schema import PlanningCreate, PlanningResponse, ConfirmedPlanCreate, ConfirmedPlanResponse
from app.services.recommendation_engine import RecommendationEngine
from app.models.planning import TreatmentPlanning, ConfirmedTreatmentPlan
import json

router = APIRouter(prefix="/planning", tags=["Treatment Planning"])

@router.post("/generate", response_model=PlanningResponse)
async def generate_plan(data: PlanningCreate, db: AsyncSession = Depends(get_db)):
    # Calculate top 3 AI recommendations via Support Vector Machine (SVM) engine
    recs = RecommendationEngine.generate_recommendations(
        data.bone_height, data.bone_width, data.bone_density, data.bite_force
    )
    
    # Extract Best Match (first entry) for backwards-compatibility fields
    best_match = recs[0]
    
    # Save to treatment_planning table
    plan_dict = data.dict()
    plan_dict.update({
        "implant_recommendation": best_match["implant_type"],
        "success_probability": best_match["success_probability"],
        "stability_prediction": best_match["stability_score"],
        "implant_recommendations": json.dumps(recs) # JSON serialize list
    })
    
    db_plan = TreatmentPlanning(**plan_dict)
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    
    return db_plan

@router.post("/confirm", response_model=ConfirmedPlanResponse)
async def confirm_plan(data: ConfirmedPlanCreate, db: AsyncSession = Depends(get_db)):
    db_confirm = ConfirmedTreatmentPlan(**data.dict())
    db.add(db_confirm)
    await db.commit()
    await db.refresh(db_confirm)
    return db_confirm
