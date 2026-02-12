"""
GBSkillEngine Schemas初始化
"""
from app.schemas.standard import (
    StandardBase,
    StandardCreate,
    StandardUpdate,
    StandardResponse,
    StandardListResponse,
    StandardUploadResponse,
    StandardCompileRequest,
    StandardCompileResponse
)
from app.schemas.skill import (
    SkillDSL,
    SkillBase,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse,
    SkillVersionResponse
)
from app.schemas.material import (
    MaterialParseRequest,
    MaterialParseBatchRequest,
    MaterialParseResult,
    MaterialParseResponse,
    ExecutionTrace,
    EngineExecutionStep,
    ParsedAttribute,
    ExecutionLogResponse,
    ExecutionLogListResponse
)
from app.schemas.kg import (
    NodeCreate,
    NodeResponse,
    RelationshipCreate,
    RelationshipResponse,
    GraphVisualizationResponse,
    CypherQueryRequest,
    CypherQueryResponse
)

__all__ = [
    # Standard
    "StandardBase",
    "StandardCreate",
    "StandardUpdate",
    "StandardResponse",
    "StandardListResponse",
    "StandardUploadResponse",
    "StandardCompileRequest",
    "StandardCompileResponse",
    # Skill
    "SkillDSL",
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "SkillListResponse",
    "SkillVersionResponse",
    # Material
    "MaterialParseRequest",
    "MaterialParseBatchRequest",
    "MaterialParseResult",
    "MaterialParseResponse",
    "ExecutionTrace",
    "EngineExecutionStep",
    "ParsedAttribute",
    "ExecutionLogResponse",
    "ExecutionLogListResponse",
    # KG
    "NodeCreate",
    "NodeResponse",
    "RelationshipCreate",
    "RelationshipResponse",
    "GraphVisualizationResponse",
    "CypherQueryRequest",
    "CypherQueryResponse"
]
