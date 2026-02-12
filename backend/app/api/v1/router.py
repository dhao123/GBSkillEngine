"""
GBSkillEngine API路由聚合
"""
from fastapi import APIRouter
from app.api.v1 import standards, skills, material_parse, knowledge_graph, observability

router = APIRouter(prefix="/api/v1")

# 注册各模块路由
router.include_router(standards.router)
router.include_router(skills.router)
router.include_router(material_parse.router)
router.include_router(knowledge_graph.router)
router.include_router(observability.router)
