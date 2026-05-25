from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class ChatbotHistory(Base):
    __tablename__ = "chatbot_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_account_id = Column(Integer, ForeignKey("patient_accounts.id"))
    message = Column(String, nullable=False)
    response = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient_account = relationship("PatientAccount", back_populates="chatbot_history")
