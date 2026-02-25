from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class TransformationLog(Base):
    __tablename__ = "transformation_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    pipeline_id = Column(String, ForeignKey("pipelines.id"), nullable=True)
    step_index = Column(Integer, nullable=False)
    operation = Column(String, nullable=False)
    column_name = Column(String, nullable=True)
    parameters = Column(Text, nullable=False)  # JSON
    rows_affected = Column(Integer, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="logs")
    pipeline = relationship("Pipeline", back_populates="logs")
