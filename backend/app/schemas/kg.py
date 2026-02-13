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


# ========== 3D图谱相关Schema ==========

class Position3D(BaseModel):
    """3D位置"""
    x: float = 0
    y: float = 0
    z: float = 0


class NodeStyle(BaseModel):
    """节点样式"""
    color: str = "#666"
    size: float = 10
    opacity: float = 1.0


class Graph3DNode(BaseModel):
    """3D图谱节点"""
    id: str
    nodeType: str = Field(..., description="节点类型: Standard|Skill|Category|Domain|TimeSlice")
    label: str = Field(..., description="显示标签")
    properties: Dict[str, Any] = Field(default_factory=dict)
    position: Position3D = Field(default_factory=Position3D)
    style: NodeStyle = Field(default_factory=NodeStyle)


class Graph3DEdge(BaseModel):
    """3D图谱边"""
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class TimeSliceInfo(BaseModel):
    """时间切片信息"""
    year: int
    z_position: float
    label: str


class DomainInfo(BaseModel):
    """领域信息"""
    domain_id: str
    domain_name: str
    color: str
    sector_angle: float


class GraphMetadata(BaseModel):
    """图谱元数据"""
    totalNodes: int = 0
    totalEdges: int = 0
    timeRange: Dict[str, Optional[int]] = Field(default_factory=lambda: {"min": None, "max": None})
    domainCount: int = 0


class Graph3DVisualizationResponse(BaseModel):
    """3D图谱可视化响应"""
    nodes: List[Graph3DNode] = Field(default_factory=list)
    edges: List[Graph3DEdge] = Field(default_factory=list)
    timeSlices: List[TimeSliceInfo] = Field(default_factory=list)
    domains: List[DomainInfo] = Field(default_factory=list)
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)


class Graph3DFilterParams(BaseModel):
    """3D图谱过滤参数"""
    start_year: Optional[int] = Field(None, description="起始年份")
    end_year: Optional[int] = Field(None, description="结束年份")
    domains: Optional[List[str]] = Field(None, description="领域过滤列表")
    limit: int = Field(500, ge=1, le=2000, description="最大节点数")
