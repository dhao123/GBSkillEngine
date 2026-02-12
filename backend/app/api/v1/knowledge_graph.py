"""
GBSkillEngine 知识图谱API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.neo4j_client import neo4j_client
from app.schemas.kg import (
    NodeCreate,
    NodeResponse,
    RelationshipCreate,
    GraphVisualizationResponse,
    CypherQueryRequest,
    CypherQueryResponse
)

router = APIRouter(prefix="/knowledge-graph", tags=["知识图谱"])


@router.get("/visualize", response_model=GraphVisualizationResponse)
async def get_graph_visualization(
    center_node_id: Optional[str] = Query(None, description="中心节点ID"),
    depth: int = Query(2, ge=1, le=5, description="遍历深度")
):
    """获取图谱可视化数据"""
    try:
        data = await neo4j_client.get_graph_data(center_node_id, depth)
        return GraphVisualizationResponse(
            nodes=[NodeResponse(**n) for n in data["nodes"]],
            edges=data["edges"]
        )
    except Exception as e:
        # Neo4j未连接时返回模拟数据
        return GraphVisualizationResponse(
            nodes=[
                NodeResponse(id="1", label="Standard", properties={"standardCode": "GB/T 4219.1-2021", "standardName": "工业用PVC-U管道系统"}),
                NodeResponse(id="2", label="Category", properties={"categoryName": "管材", "level": 1}),
                NodeResponse(id="3", label="Category", properties={"categoryName": "塑料管", "level": 2}),
                NodeResponse(id="4", label="Category", properties={"categoryName": "PVC-U管", "level": 3}),
                NodeResponse(id="5", label="Attribute", properties={"attributeName": "公称直径", "unit": "mm"}),
                NodeResponse(id="6", label="Attribute", properties={"attributeName": "公称压力", "unit": "MPa"}),
            ],
            edges=[
                {"source": "1", "target": "2", "type": "DEFINES_CATEGORY"},
                {"source": "2", "target": "3", "type": "PARENT_OF"},
                {"source": "3", "target": "4", "type": "PARENT_OF"},
                {"source": "4", "target": "5", "type": "HAS_ATTRIBUTE"},
                {"source": "4", "target": "6", "type": "HAS_ATTRIBUTE"},
            ]
        )


@router.post("/nodes", response_model=NodeResponse)
async def create_node(data: NodeCreate):
    """创建节点"""
    try:
        result = await neo4j_client.create_node(data.label, data.properties)
        return NodeResponse(
            id=str(result.get("id", "")),
            label=data.label,
            properties=data.properties
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建节点失败: {str(e)}")


@router.post("/relationships")
async def create_relationship(data: RelationshipCreate):
    """创建关系"""
    try:
        success = await neo4j_client.create_relationship(
            data.from_label,
            data.from_properties,
            data.to_label,
            data.to_properties,
            data.rel_type,
            data.rel_properties
        )
        if success:
            return {"message": "创建成功"}
        else:
            raise HTTPException(status_code=400, detail="创建关系失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建关系失败: {str(e)}")


@router.post("/query", response_model=CypherQueryResponse)
async def execute_cypher_query(request: CypherQueryRequest):
    """执行Cypher查询"""
    try:
        records = await neo4j_client.execute_query(
            request.cypher,
            request.parameters
        )
        return CypherQueryResponse(
            records=records,
            count=len(records)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
