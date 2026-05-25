from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class LoginHistory(Base):
    __tablename__ = "login_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    device_info = Column(String, nullable=True) # e.g. iOS, Android, Web
    login_status = Column(String, default="success") # e.g. success, failed

    # Relationships
    user = relationship("User", back_populates="login_histories")
