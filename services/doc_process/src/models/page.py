"""Page model"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from .base import Base


class Page(Base):
    """PPT 页面截图"""
    __tablename__ = "pages"

    id = Column(String(64), primary_key=True)
    image_url = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "image_url": self.image_url,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
