from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class TreatmentPlanning(Base):
    __tablename__ = "treatment_planning"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bone_height = Column(Float)
    bone_width = Column(Float)
    bone_density = Column(Float)
    bite_force = Column(Float)
    implant_recommendation = Column(String)
    implant_recommendations = Column(String, nullable=True) # JSON serialized list
    success_probability = Column(Float)
    stability_prediction = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="planning")

class ConfirmedTreatmentPlan(Base):
    __tablename__ = "confirmed_treatment_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    implant_type = Column(String)
    implant_diameter = Column(Float)
    implant_length = Column(Float)
    success_probability = Column(Float)
    stability_score = Column(Float)
    risk_level = Column(String)
    treatment_notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
