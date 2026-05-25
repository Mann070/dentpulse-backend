from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class XrayUpload(Base):
    __tablename__ = "xray_uploads"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    image_path = Column(String, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    analysis_status = Column(String, default="Pending") # Pending, Processing, Analyzed

    # Relationships
    patient = relationship("Patient", back_populates="xrays")
