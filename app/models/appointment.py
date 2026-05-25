from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_account_id = Column(Integer, ForeignKey("patient_accounts.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String, nullable=False)               # "2026-02-14"
    time = Column(String, nullable=False)               # "10:30 AM"
    consultation_type = Column(String, default="physical")  # physical / virtual
    status = Column(String, default="pending")          # pending / accepted / rescheduled / completed / cancelled
    meeting_link = Column(String, nullable=True)        # for virtual consultations
    patient_notes = Column(String, nullable=True)
    doctor_notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient_account = relationship("PatientAccount", back_populates="appointments")
    doctor = relationship("User")
