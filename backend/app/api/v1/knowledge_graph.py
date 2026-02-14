"""
GBSkillEngine 知识图谱API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.core.neo4j_client import neo4j_client
from app.services.knowledge_graph.sync_service import kg_sync_service
from app.schemas.kg import (
    NodeCreate,
    NodeResponse,
    RelationshipCreate,
    GraphVisualizationResponse,
    CypherQueryRequest,
    CypherQueryResponse,
    Graph3DVisualizationResponse,
    Graph3DNode,
    Graph3DEdge,
    TimeSliceInfo,
    DomainInfo,
    GraphMetadata,
    Position3D,
    NodeStyle
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


# ========== 3D图谱API ==========

@router.get("/3d/visualize", response_model=Graph3DVisualizationResponse)
async def get_3d_graph_visualization(
    start_year: Optional[int] = Query(None, description="起始年份"),
    end_year: Optional[int] = Query(None, description="结束年份"),
    domains: Optional[str] = Query(None, description="领域过滤,逗号分隔"),
    limit: int = Query(500, ge=1, le=2000, description="最大节点数")
):
    """获取3D图谱可视化数据"""
    try:
        # 解析领域参数
        domain_list = domains.split(",") if domains else None
        
        data = await kg_sync_service.get_3d_graph_data(
            start_year=start_year,
            end_year=end_year,
            domains=domain_list,
            limit=limit
        )
        
        # 如果Neo4j没有数据，返回Mock数据用于演示
        if not data["nodes"]:
            return _get_mock_3d_data()
        
        # 转换为响应模型
        nodes = [
            Graph3DNode(
                id=n["id"],
                nodeType=n["nodeType"],
                label=n["label"],
                properties=n["properties"],
                position=Position3D(**n["position"]),
                style=NodeStyle(**n["style"])
            )
            for n in data["nodes"]
        ]
        
        edges = [
            Graph3DEdge(
                source=e["source"],
                target=e["target"],
                type=e["type"]
            )
            for e in data["edges"]
        ]
        
        time_slices = [
            TimeSliceInfo(**t) for t in data["timeSlices"]
        ]
        
        domains_info = [
            DomainInfo(**d) for d in data["domains"]
        ]
        
        return Graph3DVisualizationResponse(
            nodes=nodes,
            edges=edges,
            timeSlices=time_slices,
            domains=domains_info,
            metadata=GraphMetadata(**data["metadata"])
        )
        
    except Exception as e:
        # 返回Mock数据用于开发
        return _get_mock_3d_data()


@router.get("/3d/domains", response_model=List[DomainInfo])
async def get_domains():
    """获取所有领域列表"""
    try:
        domains = await kg_sync_service.get_domains()
        return [DomainInfo(**d) for d in domains]
    except Exception as e:
        # 返回默认领域配置
        from app.services.knowledge_graph.sync_service import DEFAULT_DOMAIN_CONFIG
        return [
            DomainInfo(
                domain_id=f"domain_{k}",
                domain_name=v["name"],
                color=v["color"],
                sector_angle=v["sector_angle"]
            )
            for k, v in DEFAULT_DOMAIN_CONFIG.items()
        ]


@router.get("/3d/time-slices", response_model=List[TimeSliceInfo])
async def get_time_slices():
    """获取所有时间切片列表"""
    try:
        slices = await kg_sync_service.get_time_slices()
        return [TimeSliceInfo(**s) for s in slices]
    except Exception as e:
        # 返回默认时间切片
        from datetime import datetime
        current_year = datetime.now().year
        return [
            TimeSliceInfo(
                year=year,
                z_position=(year - 2015) * 50,
                label=f"{year}年"
            )
            for year in range(2018, current_year + 1)
        ]


def _get_mock_3d_data() -> Graph3DVisualizationResponse:
    """生成Mock 3D数据用于开发和演示
    
    包含新增实体：StandardSeries（标准系列）、SkillFamily（技能族）
    """
    import math
    
    nodes = []
    edges = []
    
    # 领域节点（位于平面外围）- 动态推断的领域
    domains_data = [
        ("domain_pipe", "管道系统", 0, "#00d4ff"),
        ("domain_fastener", "紧固件", 51, "#ff6b6b"),
        ("domain_valve", "阀门", 102, "#7c3aed"),
        ("domain_fitting", "管件", 153, "#10b981"),
        ("domain_bearing", "轴承", 204, "#f59e0b"),
        ("domain_seal", "密封件", 255, "#ec4899"),
        ("domain_cable", "电线电缆", 306, "#06b6d4"),
    ]
    
    for domain_id, name, angle, color in domains_data:
        rad = math.radians(angle)
        nodes.append(Graph3DNode(
            id=domain_id,
            nodeType="Domain",
            label=name,
            properties={"domain_name": name, "sector_angle": angle},
            position=Position3D(x=350 * math.cos(rad), y=350 * math.sin(rad), z=150),
            style=NodeStyle(color=color, size=18, opacity=1.0)
        ))
    
    # 时间切片
    time_slices = [
        TimeSliceInfo(year=y, z_position=(y - 2015) * 50, label=f"{y}年")
        for y in range(2015, 2027)
    ]
    
    # ========== 新增：标准系列（StandardSeries）节点 ==========
    series_data = [
        ("GB/T 4219", "工业用PVC-U管道系统系列", "pipe", 3),  # 包含4219.1, 4219.2, 4219.3
        ("GB/T 10002", "给水用硬PVC管系列", "pipe", 2),
        ("GB/T 18993", "冷热水用PP管系列", "pipe", 3),
        ("GB/T 5782", "六角头螺栓系列", "fastener", 1),
        ("GB/T 6170", "六角螺母系列", "fastener", 2),
        ("GB/T 12220", "阀门标志系列", "valve", 1),
        ("GB/T 12459", "对焊管件系列", "fitting", 1),
        ("GB/T 276", "深沟球轴承系列", "bearing", 1),
        ("GB/T 3452", "O型密封圈系列", "seal", 2),
    ]
    
    for series_code, series_name, domain, part_count in series_data:
        domain_cfg = next((d for d in domains_data if d[0] == f"domain_{domain}"), domains_data[0])
        base_angle = math.radians(domain_cfg[2] - 15)  # 系列节点在领域内侧
        radius = 300
        
        nodes.append(Graph3DNode(
            id=series_code,
            nodeType="StandardSeries",
            label=series_code,
            properties={
                "series_code": series_code, 
                "series_name": series_name, 
                "domain": domain,
                "part_count": part_count
            },
            position=Position3D(x=radius * math.cos(base_angle), y=radius * math.sin(base_angle), z=180),
            style=NodeStyle(color="#fbbf24", size=14, opacity=0.95)  # 金色
        ))
        edges.append(Graph3DEdge(source=series_code, target=f"domain_{domain}", type="BELONGS_TO_DOMAIN"))
    
    # 标准节点（分布在各领域，按年份分层）
    standards = [
        ("GB/T 4219.1-2021", "工业用PVC-U管道系统 第1部分", "pipe", 2021, "GB/T 4219"),
        ("GB/T 4219.2-2021", "工业用PVC-U管道系统 第2部分", "pipe", 2021, "GB/T 4219"),
        ("GB/T 4219.3-2021", "工业用PVC-U管道系统 第3部分", "pipe", 2021, "GB/T 4219"),
        ("GB/T 10002.1-2006", "给水用硬PVC管材", "pipe", 2006, "GB/T 10002"),
        ("GB/T 18993.2-2003", "冷热水用PP-R管道", "pipe", 2003, "GB/T 18993"),
        ("GB/T 13663-2018", "给水用PE管", "pipe", 2018, None),
        ("GB/T 5782-2016", "六角头螺栓", "fastener", 2016, "GB/T 5782"),
        ("GB/T 5783-2000", "六角头螺栓全螺纹", "fastener", 2000, None),
        ("GB/T 6170-2015", "1型六角螺母", "fastener", 2015, "GB/T 6170"),
        ("GB/T 97.1-2002", "平垫圈A级", "fastener", 2002, None),
        ("GB/T 12220-2015", "工业阀门标志", "valve", 2015, "GB/T 12220"),
        ("GB/T 12224-2015", "钢制阀门一般要求", "valve", 2015, None),
        ("GB/T 12238-2008", "法兰蝶阀", "valve", 2008, None),
        ("GB/T 12459-2017", "钢制对焊管件", "fitting", 2017, "GB/T 12459"),
        ("GB/T 13401-2017", "锻钢管件", "fitting", 2017, None),
        ("GB/T 276-2013", "深沟球轴承", "bearing", 2013, "GB/T 276"),
        ("GB/T 297-2015", "圆锥滚子轴承", "bearing", 2015, None),
        ("GB/T 3452.1-2005", "O型橡胶密封圈", "seal", 2005, "GB/T 3452"),
        ("GB/T 9126-2008", "管法兰用垫片", "seal", 2008, None),
        ("GB/T 5023-2008", "额定电压电缆", "cable", 2008, None),
        ("GB/T 12706-2020", "额定电力电缆", "cable", 2020, None),
    ]
    
    for std_code, std_name, domain, year, series_code in standards:
        domain_cfg = next((d for d in domains_data if d[0] == f"domain_{domain}"), domains_data[0])
        base_angle = math.radians(domain_cfg[2])
        offset = hash(std_code) % 20 - 10
        angle = base_angle + math.radians(offset)
        radius = 180 + (hash(std_code) % 60)
        z = (year - 2015) * 50
        
        nodes.append(Graph3DNode(
            id=std_code,
            nodeType="Standard",
            label=std_code.split("-")[0],
            properties={
                "standard_code": std_code, 
                "standard_name": std_name, 
                "domain": domain, 
                "version_year": year,
                "series_code": series_code
            },
            position=Position3D(x=radius * math.cos(angle), y=radius * math.sin(angle), z=z),
            style=NodeStyle(color="#00d4ff", size=10, opacity=0.9)
        ))
        edges.append(Graph3DEdge(source=std_code, target=f"domain_{domain}", type="BELONGS_TO_DOMAIN"))
        # 如果属于系列，创建PART_OF_SERIES关系
        if series_code:
            edges.append(Graph3DEdge(source=std_code, target=series_code, type="PART_OF_SERIES"))
    
    # 类目节点
    categories = [
        ("cat_pipe_1", "管材", "pipe", 1),
        ("cat_pipe_2", "塑料管", "pipe", 2),
        ("cat_pipe_3", "PVC-U管", "pipe", 3),
        ("cat_pipe_3b", "PE管", "pipe", 3),
        ("cat_pipe_3c", "PP-R管", "pipe", 3),
        ("cat_fast_1", "紧固件", "fastener", 1),
        ("cat_fast_2", "螺栓", "fastener", 2),
        ("cat_fast_2b", "螺母", "fastener", 2),
        ("cat_fast_2c", "垫圈", "fastener", 2),
        ("cat_valve_1", "阀门", "valve", 1),
        ("cat_valve_2", "蝶阀", "valve", 2),
        ("cat_valve_2b", "闸阀", "valve", 2),
        ("cat_fitting_1", "管件", "fitting", 1),
        ("cat_bearing_1", "轴承", "bearing", 1),
        ("cat_seal_1", "密封件", "seal", 1),
        ("cat_cable_1", "电线电缆", "cable", 1),
    ]
    
    for cat_id, cat_name, domain, level in categories:
        domain_cfg = next((d for d in domains_data if d[0] == f"domain_{domain}"), domains_data[0])
        base_angle = math.radians(domain_cfg[2])
        offset = hash(cat_id) % 15 - 7
        angle = base_angle + math.radians(offset)
        radius = 280 + level * 15
        
        nodes.append(Graph3DNode(
            id=cat_id,
            nodeType="Category",
            label=cat_name,
            properties={"category_name": cat_name, "level": level, "domain": domain},
            position=Position3D(x=radius * math.cos(angle), y=radius * math.sin(angle), z=200),
            style=NodeStyle(color="#7c3aed", size=7, opacity=0.8)
        ))
    
    # 类目层级关系
    cat_edges = [
        ("cat_pipe_1", "cat_pipe_2"), ("cat_pipe_2", "cat_pipe_3"),
        ("cat_pipe_2", "cat_pipe_3b"), ("cat_pipe_2", "cat_pipe_3c"),
        ("cat_fast_1", "cat_fast_2"), ("cat_fast_1", "cat_fast_2b"), ("cat_fast_1", "cat_fast_2c"),
        ("cat_valve_1", "cat_valve_2"), ("cat_valve_1", "cat_valve_2b"),
    ]
    for src, tgt in cat_edges:
        edges.append(Graph3DEdge(source=src, target=tgt, type="PARENT_OF"))
    
    # ========== 新增：技能族（SkillFamily）节点 ==========
    skill_families = [
        ("family_GBT_4219", "PVC-U管道技能族", "pipe", "GB/T 4219"),
        ("family_GBT_5782", "六角螺栓技能族", "fastener", "GB/T 5782"),
        ("family_GBT_12220", "阀门标志技能族", "valve", "GB/T 12220"),
        ("family_GBT_276", "深沟球轴承技能族", "bearing", "GB/T 276"),
    ]
    
    for family_code, family_name, domain, series_code in skill_families:
        domain_cfg = next((d for d in domains_data if d[0] == f"domain_{domain}"), domains_data[0])
        base_angle = math.radians(domain_cfg[2] + 20)  # 技能族在领域另一侧
        radius = 120
        
        nodes.append(Graph3DNode(
            id=family_code,
            nodeType="SkillFamily",
            label=family_name,
            properties={
                "family_code": family_code,
                "family_name": family_name,
                "domain": domain,
                "series_code": series_code
            },
            position=Position3D(x=radius * math.cos(base_angle), y=radius * math.sin(base_angle), z=220),
            style=NodeStyle(color="#34d399", size=12, opacity=0.95)  # 绿色
        ))
        # 技能族与系列的关系
        edges.append(Graph3DEdge(source=family_code, target=series_code, type="FAMILY_FROM_SERIES"))
    
    # Skill节点
    skills = [
        ("skill_gb_t_4219_1", "PVC-U管材Skill-1", "pipe", 2021, "GB/T 4219.1-2021", "family_GBT_4219"),
        ("skill_gb_t_4219_2", "PVC-U管材Skill-2", "pipe", 2021, "GB/T 4219.2-2021", "family_GBT_4219"),
        ("skill_gb_t_5782", "六角螺栓Skill", "fastener", 2016, "GB/T 5782-2016", "family_GBT_5782"),
        ("skill_gb_t_12220", "阀门标志Skill", "valve", 2015, "GB/T 12220-2015", "family_GBT_12220"),
        ("skill_gb_t_13663", "PE管材Skill", "pipe", 2018, "GB/T 13663-2018", None),
        ("skill_gb_t_276", "深沟球轴承Skill", "bearing", 2013, "GB/T 276-2013", "family_GBT_276"),
    ]
    
    for skill_id, skill_name, domain, year, std_code, family_code in skills:
        domain_cfg = next((d for d in domains_data if d[0] == f"domain_{domain}"), domains_data[0])
        angle = math.radians(domain_cfg[2] + 8)
        z = (year - 2015) * 50 + 25
        
        nodes.append(Graph3DNode(
            id=skill_id,
            nodeType="Skill",
            label=skill_name,
            properties={"skill_id": skill_id, "skill_name": skill_name, "domain": domain},
            position=Position3D(x=150 * math.cos(angle), y=150 * math.sin(angle), z=z),
            style=NodeStyle(color="#ff6b6b", size=9, opacity=0.9)
        ))
        edges.append(Graph3DEdge(source=std_code, target=skill_id, type="COMPILES_TO"))
        edges.append(Graph3DEdge(source=skill_id, target=f"domain_{domain}", type="BELONGS_TO_DOMAIN"))
        # 如果属于技能族，创建BELONGS_TO_FAMILY关系
        if family_code:
            edges.append(Graph3DEdge(source=skill_id, target=family_code, type="BELONGS_TO_FAMILY"))
    
    domains_info = [
        DomainInfo(domain_id=d[0], domain_name=d[1], color=d[3], sector_angle=d[2])
        for d in domains_data
    ]
    
    return Graph3DVisualizationResponse(
        nodes=nodes,
        edges=edges,
        timeSlices=time_slices,
        domains=domains_info,
        metadata=GraphMetadata(
            totalNodes=len(nodes),
            totalEdges=len(edges),
            timeRange={"min": 2003, "max": 2026},
            domainCount=len(domains_data)
        )
    )
