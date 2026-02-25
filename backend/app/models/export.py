from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class Export(Base):
    __tablename__ = "exports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    pipeline_id = Column(String, ForeignKey("pipelines.id"), nullable=True)
    format = Column(String, nullable=False)  # csv, xlsx, json
    file_path = Column(String, nullable=False)
    include_log = Column(Boolean, default=False)
    include_pipeline = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="exports")
    pipeline = relationship("Pipeline", back_populates="exports")
