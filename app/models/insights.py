from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Insights(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    complication_risk = Column(String)
    ai_confidence = Column(String)
    recommendation = Column(String)
    alert_level = Column(String)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="insights")
