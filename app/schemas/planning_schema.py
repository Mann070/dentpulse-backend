from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PlanningBase(BaseModel):
    bone_height: float
    bone_width: float
    bone_density: float
    bite_force: float

class PlanningCreate(PlanningBase):
    patient_id: int
    doctor_id: Optional[int] = None

class PlanningResponse(PlanningBase):
    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    implant_recommendation: str
    success_probability: float
    stability_prediction: float
    implant_recommendations: Optional[str] = None  # JSON serialized string

    class Config:
        from_attributes = True

class ConfirmedPlanCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    implant_type: str
    implant_diameter: float
    implant_length: float
    success_probability: float
    stability_score: float
    risk_level: str
    treatment_notes: Optional[str] = None

class ConfirmedPlanResponse(ConfirmedPlanCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
