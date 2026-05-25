from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Monitoring(Base):
    __tablename__ = "monitoring"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bone_loss = Column(Float)
    isq_score = Column(Float)
    pain_level = Column(Integer)
    swelling = Column(String)
    bleeding = Column(String)
    mobility = Column(String)
    uploaded_scan = Column(String, nullable=True)
    cnn_result = Column(String, nullable=True)
    svm_prediction = Column(String, nullable=True)
    monitoring_date = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="monitoring")
