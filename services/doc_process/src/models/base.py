"""SQLAlchemy base and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from functools import lru_cache

from ..config import get_settings

Base = declarative_base()


@lru_cache()
def get_engine():
    """获取数据库引擎单例"""
    settings = get_settings()
    return create_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,  # 检查连接是否有效
        echo=False  # 生产环境不打印 SQL
    )


def get_session_factory():
    """获取 Session 工厂"""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: 获取数据库 session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
