"""
GBSkillEngine - MRO国标技能引擎平台

FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.core.database import init_db, close_db
from app.core.neo4j_client import neo4j_client
from app.api.v1.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("正在初始化数据库...")
    await init_db()
    print("数据库初始化完成")
    
    yield
    
    # 关闭时
    print("正在关闭连接...")
    await close_db()
    await neo4j_client.close()
    print("连接已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="GBSkillEngine",
    description="MRO国标技能引擎平台 - 国标 → Skill 编译 → 知识图谱 → 物料标准化梳理",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router)


@app.get("/", tags=["健康检查"])
async def root():
    """根路径 - 健康检查"""
    return {
        "name": "GBSkillEngine",
        "version": "1.0.0",
        "status": "running",
        "message": "MRO国标技能引擎平台"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "database": "connected",
        "neo4j": "connected"
    }
