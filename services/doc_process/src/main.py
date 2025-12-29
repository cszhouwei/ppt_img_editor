import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .storage.minio_client import get_minio_client
from .models.base import get_engine, Base
from .api import health, assets, pages, projects

# 配置日志
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting up doc_process service...")

    # 初始化数据库表
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # 初始化 MinIO 连接
    try:
        minio_client = get_minio_client()
        logger.info(f"MinIO client initialized. Bucket: {settings.s3_bucket}")
    except Exception as e:
        logger.error(f"Failed to initialize MinIO: {e}")
        raise

    yield

    logger.info("Shutting down doc_process service...")


# 创建 FastAPI 应用
app = FastAPI(
    title="PPT Screenshot Text Editor - Doc Process Service",
    description="Document processing service for OCR, patch generation, and project management",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, tags=["health"])
app.include_router(assets.router, prefix="/v1/assets", tags=["assets"])
app.include_router(pages.router, prefix="/v1/pages", tags=["pages"])
app.include_router(projects.router, prefix="/v1/projects", tags=["projects"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "doc_process",
        "version": "0.1.0",
        "status": "running"
    }
