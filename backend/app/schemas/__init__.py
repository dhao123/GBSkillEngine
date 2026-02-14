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

# 新增Schema
from app.schemas.domain import (
    DomainBase,
    DomainCreate,
    DomainUpdate,
    DomainResponse,
    DomainListResponse,
    DomainWithStats
)
from app.schemas.standard_series import (
    StandardSeriesBase,
    StandardSeriesCreate,
    StandardSeriesUpdate,
    StandardSeriesResponse,
    StandardSeriesListResponse,
    StandardSeriesWithStandards,
    SeriesDetectionResult
)
from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    CategoryTreeNode,
    CategoryTree,
    CategoryHierarchy
)
from app.schemas.skill_family import (
    SkillFamilyBase,
    SkillFamilyCreate,
    SkillFamilyUpdate,
    SkillFamilyResponse,
    SkillFamilyListResponse,
    SkillFamilyMemberBase,
    SkillFamilyMemberCreate,
    SkillFamilyMemberResponse,
    SkillFamilyWithMembers
)
from app.schemas.attribute_definition import (
    AttributeDefinitionBase,
    AttributeDefinitionCreate,
    AttributeDefinitionUpdate,
    AttributeDefinitionResponse,
    AttributeDefinitionListResponse,
    DomainAttributeBase,
    DomainAttributeCreate,
    DomainAttributeResponse,
    DomainAttributeWithDetails,
    AttributeByDomain
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
    "CypherQueryResponse",
    # Domain
    "DomainBase",
    "DomainCreate",
    "DomainUpdate",
    "DomainResponse",
    "DomainListResponse",
    "DomainWithStats",
    # StandardSeries
    "StandardSeriesBase",
    "StandardSeriesCreate",
    "StandardSeriesUpdate",
    "StandardSeriesResponse",
    "StandardSeriesListResponse",
    "StandardSeriesWithStandards",
    "SeriesDetectionResult",
    # Category
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryListResponse",
    "CategoryTreeNode",
    "CategoryTree",
    "CategoryHierarchy",
    # SkillFamily
    "SkillFamilyBase",
    "SkillFamilyCreate",
    "SkillFamilyUpdate",
    "SkillFamilyResponse",
    "SkillFamilyListResponse",
    "SkillFamilyMemberBase",
    "SkillFamilyMemberCreate",
    "SkillFamilyMemberResponse",
    "SkillFamilyWithMembers",
    # AttributeDefinition
    "AttributeDefinitionBase",
    "AttributeDefinitionCreate",
    "AttributeDefinitionUpdate",
    "AttributeDefinitionResponse",
    "AttributeDefinitionListResponse",
    "DomainAttributeBase",
    "DomainAttributeCreate",
    "DomainAttributeResponse",
    "DomainAttributeWithDetails",
    "AttributeByDomain",
]
