from pydantic import BaseModel
from datetime import datetime

class InsightBase(BaseModel):
    complication_risk: str
    ai_confidence: str
    recommendation: str
    alert_level: str

class InsightCreate(InsightBase):
    patient_id: int

class InsightResponse(InsightBase):
    id: int
    patient_id: int
    generated_at: datetime

    class Config:
        from_attributes = True
