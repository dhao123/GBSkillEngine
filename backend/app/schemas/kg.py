"""
GBSkillEngine 知识图谱相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NodeCreate(BaseModel):
    """创建节点请求"""
    label: str = Field(..., description="节点标签", example="Standard")
    properties: Dict[str, Any] = Field(..., description="节点属性")


class NodeResponse(BaseModel):
    """节点响应"""
    id: str
    label: str
    properties: Dict[str, Any]


class RelationshipCreate(BaseModel):
    """创建关系请求"""
    from_label: str
    from_properties: Dict[str, Any]
    to_label: str
    to_properties: Dict[str, Any]
    rel_type: str
    rel_properties: Optional[Dict[str, Any]] = None


class RelationshipResponse(BaseModel):
    """关系响应"""
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class GraphVisualizationResponse(BaseModel):
    """图谱可视化响应"""
    nodes: List[NodeResponse]
    edges: List[RelationshipResponse]


class CypherQueryRequest(BaseModel):
    """Cypher查询请求"""
    cypher: str = Field(..., description="Cypher查询语句")
    parameters: Optional[Dict[str, Any]] = Field(None, description="查询参数")


class CypherQueryResponse(BaseModel):
    """Cypher查询响应"""
    records: List[Dict[str, Any]]
    count: int
