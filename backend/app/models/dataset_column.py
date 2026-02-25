from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    name = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    detected_type = Column(String, nullable=False)  # Text, Numeric, Date, Boolean, Categorical
    overridden_type = Column(String, nullable=True)
    null_count = Column(Integer, nullable=False)
    null_pct = Column(Float, nullable=False)
    unique_count = Column(Integer, nullable=False)
    min_val = Column(String, nullable=True)
    max_val = Column(String, nullable=True)
    mean_val = Column(Float, nullable=True)
    top_values = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="columns")
