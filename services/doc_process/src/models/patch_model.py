"""Patch model"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Float
from .base import Base


class Patch(Base):
    """文字抹除后的背景 patch"""
    __tablename__ = "patches"

    id = Column(String(64), primary_key=True)
    page_id = Column(String(64), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(64), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)
    bbox = Column(JSON, nullable=False)  # {"x": 110, "y": 72, "w": 440, "h": 84}
    image_url = Column(String, nullable=False)
    debug_info = Column(JSON, nullable=True)  # {"bg_model": "solid", "mae": 6.1, ...}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "bbox": self.bbox,
            "image_url": self.image_url,
            "debug_info": self.debug_info,
        }
