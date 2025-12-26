"""Candidate model"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from .base import Base


class Candidate(Base):
    """OCR 识别的文字候选框"""
    __tablename__ = "candidates"

    id = Column(String(64), primary_key=True)
    page_id = Column(String(64), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    quad = Column(JSON, nullable=False)  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    bbox = Column(JSON, nullable=False)  # {"x": 120, "y": 80, "w": 420, "h": 64}
    angle_deg = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "text": self.text,
            "confidence": self.confidence,
            "quad": self.quad,
            "bbox": self.bbox,
            "angle_deg": self.angle_deg,
        }
