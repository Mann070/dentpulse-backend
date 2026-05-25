from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class PatientAccount(Base):
    __tablename__ = "patient_accounts"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)  # Male, Female, Other
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="patient")
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime(timezone=True), nullable=True)
    otp_retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    appointments = relationship(
        "Appointment", back_populates="patient_account", cascade="all, delete-orphan"
    )
    prescriptions = relationship(
        "Prescription", back_populates="patient_account", cascade="all, delete-orphan"
    )
    chatbot_history = relationship(
        "ChatbotHistory", back_populates="patient_account", cascade="all, delete-orphan"
    )

    @property
    def name(self):
        return self.full_name
