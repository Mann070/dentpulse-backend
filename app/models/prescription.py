from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_account_id = Column(Integer, ForeignKey("patient_accounts.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    medicine_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)         # e.g. "500mg twice daily"
    instructions = Column(String, nullable=True)
    duration = Column(String, nullable=True)        # e.g. "7 days"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient_account = relationship("PatientAccount", back_populates="prescriptions")
    doctor = relationship("User")
