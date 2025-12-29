"""Project model for storing editor state"""
from sqlalchemy import Column, String, JSON, DateTime
from datetime import datetime
from .base import Base


class Project(Base):
    """
    Project 保存编辑器状态

    包含:
    - page 信息 (image_url, width, height)
    - layers 数组 (patch layers + text layers)
    """
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)

    # Page 信息
    page_data = Column(JSON, nullable=False)  # {"page_id": "...", "image_url": "...", "width": 1920, "height": 1080}

    # Layers 数组
    layers = Column(JSON, nullable=False, default=list)  # [{"id": "...", "kind": "patch|text", ...}]

    # 元数据
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to API response format"""
        return {
            "project_id": self.id,
            "page": self.page_data,
            "layers": self.layers,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
