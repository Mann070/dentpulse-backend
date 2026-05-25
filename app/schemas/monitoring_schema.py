from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MonitoringBase(BaseModel):
    bone_loss: float
    isq_score: float
    pain_level: int
    swelling: str
    bleeding: str
    mobility: str
    doctor_id: Optional[int] = None
    uploaded_scan: Optional[str] = None
    cnn_result: Optional[str] = None
    svm_prediction: Optional[str] = None

class MonitoringCreate(MonitoringBase):
    patient_id: int

class MonitoringResponse(MonitoringBase):
    id: int
    patient_id: int
    monitoring_date: datetime

    class Config:
        from_attributes = True
