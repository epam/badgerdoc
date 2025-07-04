from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SynchronizationStatus(str, Enum):
    """Enum for synchronization status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Synchronization(Base):
    """Model representing a Veeva PM synchronization run."""
    
    __tablename__ = "veeva_pm_synchronization_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    configuration_id = Column(Integer, ForeignKey("veeva_pm_configurations.id", ondelete="CASCADE"), nullable=False)
    status = Column(SynchronizationStatus, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False, onupdate=func.now())
    
    # Relationship with the Configuration model
    configuration = relationship("Configuration", back_populates="synchronizations")
    
    def __repr__(self):
        return f"<Synchronization(id={self.id}, configuration_id={self.configuration_id}, status={self.status})>"