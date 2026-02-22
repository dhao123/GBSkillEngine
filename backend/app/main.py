"""
GBSkillEngine - MRO国标技能引擎平台

FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from app.config import settings
from app.core.database import init_db, close_db
from app.core.neo4j_client import neo4j_client
from app.core.exceptions import setup_exception_handlers
from app.api.v1.router import router as api_router


# API标签元数据
tags_metadata = [
    {
        "name": "健康检查",
        "description": "系统健康状态检查接口",
    },
    {
        "name": "国标管理",
        "description": "国家标准文档的上传、管理和编译操作",
    },
    {
        "name": "Skill管理",
        "description": "Skill DSL配置的创建、编辑、版本管理和执行",
    },
    {
        "name": "物料梳理",
        "description": "基于Skill规则的物料名称标准化解析和属性提取",
    },
    {
        "name": "知识图谱",
        "description": "Neo4j知识图谱数据查询和可视化",
    },
    {
        "name": "可观测性",
        "description": "执行日志、系统指标和追踪数据查询",
    },
]


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
    title="GBSkillsEngine API",
    description="""
## MRO国标技能引擎平台

GBSkillsEngine 是一个面向MRO(维护、维修、运营)领域的国标技能引擎平台，
实现从国家标准到Skills DSL的自动编译，并通过知识图谱实现物料的标准化梳理。

### 核心功能

- **国标管理**: 上传和管理国家标准文档(PDF/Word)
- **Skill编译**: 将国标自动编译为结构化的Skill DSL配置
- **知识图谱**: 基于Neo4j的标准知识图谱构建和查询
- **物料梳理**: 基于Skill规则的物料名称解析和属性提取
- **执行追踪**: 完整的执行日志和审计追踪

### 技术架构

- 后端: FastAPI + PostgreSQL + Neo4j
- 前端: React + TypeScript + Ant Design
- 部署: Docker Compose

### 认证说明

当前版本暂未启用认证，所有接口公开访问。生产环境部署时请配置适当的认证机制。
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "QA-Team",
        "email": "donghao.zhang@zkh.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
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

# 配置全局异常处理
setup_exception_handlers(app)


@app.get("/", tags=["健康检查"])
async def root():
    """根路径 - 健康检查"""
    return {
        "name": "GBSkillsEngine",
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
