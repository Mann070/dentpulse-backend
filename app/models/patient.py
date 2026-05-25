from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    notes = Column(String)
    implant_site = Column(String)
    implant_type = Column(String)
    surgery_date = Column(Date)
    risk_level = Column(String, default="Low")
    doctor_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    doctor = relationship("User", back_populates="patients")
    planning = relationship("TreatmentPlanning", back_populates="patient", cascade="all, delete-orphan")
    monitoring = relationship("Monitoring", back_populates="patient", cascade="all, delete-orphan")
    insights = relationship("Insights", back_populates="patient", cascade="all, delete-orphan")
    xrays = relationship("XrayUpload", back_populates="patient", cascade="all, delete-orphan")
