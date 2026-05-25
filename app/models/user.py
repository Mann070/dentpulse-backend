from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    specialization = Column(String)
    clinic_name = Column(String)
    role = Column(String, default="doctor") # doctor, admin
    phone_number = Column(String, nullable=True)
    license_id = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approval_status = Column(String, default="pending") # pending, approved, rejected
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime(timezone=True), nullable=True)
    otp_retry_count = Column(Integer, default=0)
    reset_password_otp = Column(String, nullable=True)
    reset_password_expiry = Column(DateTime(timezone=True), nullable=True)
    reset_otp_retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patients = relationship("Patient", back_populates="doctor")
    login_histories = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")

    @property
    def name(self):
        return self.full_name
