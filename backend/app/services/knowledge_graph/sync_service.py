"""
GBSkillEngine 知识图谱同步服务

负责将Standard和Skill数据同步到Neo4j知识图谱
支持动态领域、标准系列、技能族等新实体
"""
import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.neo4j_client import neo4j_client
from app.models.standard import Standard
from app.models.skill import Skill

logger = logging.getLogger(__name__)

# 默认领域配置 - 仅作为数据库为空时的后备方案
# 正式环境领域应由LLM从国标文件推断后写入数据库
DEFAULT_DOMAIN_CONFIG = {
    "general": {
        "name": "通用",
        "color": "#6b7280",
        "sector_angle": 0
    }
}

# 节点类型颜色配置
NODE_COLORS = {
    "Standard": "#00d4ff",
    "Skill": "#ff6b6b",
    "Category": "#7c3aed",
    "Domain": "#f59e0b",
    "TimeSlice": "#6366f1",
    "StandardSeries": "#fbbf24",  # 金色
    "SkillFamily": "#34d399"      # 绿色
}

# 时间基准年份（用于计算Z坐标）
BASE_YEAR = 2015
Z_SCALE = 50  # 每年的Z轴高度


class KnowledgeGraphSyncService:
    """知识图谱同步服务"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化Neo4j Schema（创建约束和索引）"""
        if self._initialized:
            return
        
        try:
            # 创建唯一性约束
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Standard) REQUIRE s.standard_code IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (sk:Skill) REQUIRE sk.skill_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.domain_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TimeSlice) REQUIRE t.year IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.category_id IS UNIQUE",
                # 新增实体约束
                "CREATE CONSTRAINT IF NOT EXISTS FOR (ss:StandardSeries) REQUIRE ss.series_code IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (sf:SkillFamily) REQUIRE sf.family_code IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await neo4j_client.execute_query(constraint)
                except Exception as e:
                    # 约束可能已存在
                    logger.debug(f"约束创建跳过: {e}")
            
            # 创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (s:Standard) ON (s.domain)",
                "CREATE INDEX IF NOT EXISTS FOR (sk:Skill) ON (sk.domain)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Category) ON (c.level)",
                # 新增索引
                "CREATE INDEX IF NOT EXISTS FOR (ss:StandardSeries) ON (ss.domain_id)",
                "CREATE INDEX IF NOT EXISTS FOR (sf:SkillFamily) ON (sf.domain_id)",
            ]
            
            for index in indexes:
                try:
                    await neo4j_client.execute_query(index)
                except Exception as e:
                    logger.debug(f"索引创建跳过: {e}")
            
            self._initialized = True
            logger.info("Neo4j Schema初始化完成")
            
        except Exception as e:
            logger.warning(f"Neo4j Schema初始化失败（可能未连接）: {e}")
    
    def _calculate_position(self, domain: str, year: int, offset: float = 0,
                             domain_config: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """计算节点的3D位置
        
        Args:
            domain: 领域标识
            year: 年份（用于Z轴）
            offset: 在领域内的偏移量
            domain_config: 领域配置（包含sector_angle），如未提供则使用默认值
            
        Returns:
            包含x, y, z的位置字典
        """
        # 如果提供了domain_config，使用其中的sector_angle
        if domain_config:
            angle = math.radians(domain_config.get("sector_angle", 0))
        else:
            # 默认使用通用配置
            default_config = DEFAULT_DOMAIN_CONFIG.get(domain, DEFAULT_DOMAIN_CONFIG["general"])
            angle = math.radians(default_config.get("sector_angle", 0))
        
        # 基础半径
        radius = 200 + offset * 30
        
        # X-Y平面位置（极坐标转笛卡尔）
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        # Z轴位置（基于年份）
        z = (year - BASE_YEAR) * Z_SCALE if year else 0
        
        return {"x": x, "y": y, "z": z}
    
    async def ensure_domain_node(self, domain: str, 
                                   domain_name: Optional[str] = None,
                                   color: Optional[str] = None,
                                   sector_angle: Optional[float] = None) -> str:
        """确保领域节点存在
        
        Args:
            domain: 领域标识（domain_code）
            domain_name: 领域名称（可选，如未提供则使用domain作为名称）
            color: 领域颜色（可选，如未提供则使用默认颜色）
            sector_angle: 扇区角度（可选）
            
        Returns:
            领域节点ID
        """
        # 使用提供的参数或默认值
        default_config = DEFAULT_DOMAIN_CONFIG.get(domain, DEFAULT_DOMAIN_CONFIG["general"])
        actual_name = domain_name or default_config.get("name", domain)
        actual_color = color or default_config.get("color", "#6b7280")
        actual_angle = sector_angle if sector_angle is not None else default_config.get("sector_angle", 0)
        
        domain_id = f"domain_{domain}"
        
        query = """
        MERGE (d:Domain {domain_id: $domain_id})
        ON CREATE SET 
            d.domain_name = $domain_name,
            d.color = $color,
            d.sector_angle = $sector_angle,
            d.created_at = datetime()
        RETURN d.domain_id as id
        """
        
        try:
            result = await neo4j_client.execute_query(query, {
                "domain_id": domain_id,
                "domain_name": actual_name,
                "color": actual_color,
                "sector_angle": actual_angle
            })
            return result[0]["id"] if result else domain_id
        except Exception as e:
            logger.warning(f"创建领域节点失败: {e}")
            return domain_id
    
    async def ensure_time_slice(self, year: int) -> str:
        """确保时间切片节点存在
        
        Args:
            year: 年份
            
        Returns:
            时间切片节点ID
        """
        if not year:
            year = datetime.now().year
        
        z_position = (year - BASE_YEAR) * Z_SCALE
        
        query = """
        MERGE (t:TimeSlice {year: $year})
        ON CREATE SET 
            t.z_position = $z_position,
            t.label = $label,
            t.created_at = datetime()
        RETURN t.year as id
        """
        
        try:
            result = await neo4j_client.execute_query(query, {
                "year": year,
                "z_position": z_position,
                "label": f"{year}年"
            })
            return str(result[0]["id"]) if result else str(year)
        except Exception as e:
            logger.warning(f"创建时间切片节点失败: {e}")
            return str(year)
    
    async def sync_standard(self, standard: Standard) -> Optional[str]:
        """同步Standard到Neo4j
        
        Args:
            standard: Standard模型实例
            
        Returns:
            创建的节点ID，失败返回None
        """
        await self.initialize()
        
        try:
            # 解析年份
            year = None
            if standard.version_year:
                try:
                    year = int(standard.version_year)
                except ValueError:
                    year = datetime.now().year
            else:
                year = standard.created_at.year if standard.created_at else datetime.now().year
            
            domain = standard.domain or "general"
            position = self._calculate_position(domain, year)
            
            # 确保领域和时间切片节点存在
            await self.ensure_domain_node(domain)
            await self.ensure_time_slice(year)
            
            # 创建Standard节点
            query = """
            MERGE (s:Standard {standard_code: $standard_code})
            ON CREATE SET 
                s.standard_name = $standard_name,
                s.version_year = $version_year,
                s.domain = $domain,
                s.status = $status,
                s.x = $x,
                s.y = $y,
                s.z = $z,
                s.color = $color,
                s.created_at = datetime()
            ON MATCH SET
                s.standard_name = $standard_name,
                s.version_year = $version_year,
                s.domain = $domain,
                s.status = $status,
                s.x = $x,
                s.y = $y,
                s.z = $z,
                s.updated_at = datetime()
            RETURN s.standard_code as id
            """
            
            result = await neo4j_client.execute_query(query, {
                "standard_code": standard.standard_code,
                "standard_name": standard.standard_name,
                "version_year": year,
                "domain": domain,
                "status": standard.status.value if standard.status else "draft",
                "x": position["x"],
                "y": position["y"],
                "z": position["z"],
                "color": NODE_COLORS["Standard"]
            })
            
            # 创建与Domain的关系
            await neo4j_client.execute_query("""
                MATCH (s:Standard {standard_code: $standard_code})
                MATCH (d:Domain {domain_id: $domain_id})
                MERGE (s)-[:BELONGS_TO_DOMAIN]->(d)
            """, {
                "standard_code": standard.standard_code,
                "domain_id": f"domain_{domain}"
            })
            
            # 创建与TimeSlice的关系
            await neo4j_client.execute_query("""
                MATCH (s:Standard {standard_code: $standard_code})
                MATCH (t:TimeSlice {year: $year})
                MERGE (s)-[:BELONGS_TO_TIME]->(t)
            """, {
                "standard_code": standard.standard_code,
                "year": year
            })
            
            logger.info(f"Standard同步到Neo4j成功: {standard.standard_code}")
            return result[0]["id"] if result else None
            
        except Exception as e:
            logger.error(f"Standard同步到Neo4j失败: {e}")
            return None
    
    async def build_category_hierarchy(
        self, 
        category_mapping: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """构建类目层级节点
        
        Args:
            category_mapping: 类目映射配置
            domain: 所属领域
            
        Returns:
            创建的类目节点ID列表
        """
        created_ids = []
        
        levels = [
            ("primaryCategory", 1),
            ("secondaryCategory", 2),
            ("tertiaryCategory", 3),
            ("quaternaryCategory", 4)
        ]
        
        parent_id = None
        
        for field, level in levels:
            category_name = category_mapping.get(field)
            if not category_name:
                continue
            
            # 生成类目ID
            category_id = f"cat_{domain}_{level}_{category_name.replace(' ', '_')}"
            
            # 计算位置（类目在领域内按层级偏移）
            year = datetime.now().year
            position = self._calculate_position(domain, year, offset=level)
            
            query = """
            MERGE (c:Category {category_id: $category_id})
            ON CREATE SET 
                c.category_name = $category_name,
                c.level = $level,
                c.domain = $domain,
                c.x = $x,
                c.y = $y,
                c.z = $z,
                c.color = $color,
                c.created_at = datetime()
            RETURN c.category_id as id
            """
            
            try:
                result = await neo4j_client.execute_query(query, {
                    "category_id": category_id,
                    "category_name": category_name,
                    "level": level,
                    "domain": domain,
                    "x": position["x"],
                    "y": position["y"],
                    "z": position["z"],
                    "color": NODE_COLORS["Category"]
                })
                
                if result:
                    created_ids.append(result[0]["id"])
                
                # 创建父子关系
                if parent_id:
                    await neo4j_client.execute_query("""
                        MATCH (parent:Category {category_id: $parent_id})
                        MATCH (child:Category {category_id: $child_id})
                        MERGE (parent)-[:PARENT_OF]->(child)
                    """, {
                        "parent_id": parent_id,
                        "child_id": category_id
                    })
                
                parent_id = category_id
                
            except Exception as e:
                logger.warning(f"创建类目节点失败: {e}")
        
        return created_ids
    
    async def sync_skill(self, skill: Skill, standard: Standard) -> Optional[str]:
        """同步Skill到Neo4j
        
        Args:
            skill: Skill模型实例
            standard: 关联的Standard模型实例
            
        Returns:
            创建的节点ID，失败返回None
        """
        await self.initialize()
        
        try:
            domain = skill.domain or standard.domain or "general"
            
            # 解析年份
            year = None
            if standard.version_year:
                try:
                    year = int(standard.version_year)
                except ValueError:
                    year = datetime.now().year
            else:
                year = datetime.now().year
            
            position = self._calculate_position(domain, year, offset=0.5)
            
            # 确保Standard节点已同步
            await self.sync_standard(standard)
            
            # 创建Skill节点
            query = """
            MERGE (sk:Skill {skill_id: $skill_id})
            ON CREATE SET 
                sk.skill_name = $skill_name,
                sk.domain = $domain,
                sk.version = $version,
                sk.status = $status,
                sk.x = $x,
                sk.y = $y,
                sk.z = $z,
                sk.color = $color,
                sk.created_at = datetime()
            ON MATCH SET
                sk.skill_name = $skill_name,
                sk.domain = $domain,
                sk.version = $version,
                sk.status = $status,
                sk.x = $x,
                sk.y = $y,
                sk.z = $z,
                sk.updated_at = datetime()
            RETURN sk.skill_id as id
            """
            
            result = await neo4j_client.execute_query(query, {
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "domain": domain,
                "version": skill.dsl_version or "1.0.0",
                "status": skill.status.value if skill.status else "draft",
                "x": position["x"],
                "y": position["y"],
                "z": position["z"],
                "color": NODE_COLORS["Skill"]
            })
            
            # 创建Standard -> Skill关系
            await neo4j_client.execute_query("""
                MATCH (s:Standard {standard_code: $standard_code})
                MATCH (sk:Skill {skill_id: $skill_id})
                MERGE (s)-[:COMPILES_TO]->(sk)
            """, {
                "standard_code": standard.standard_code,
                "skill_id": skill.skill_id
            })
            
            # 创建类目层级
            dsl = skill.dsl_content or {}
            category_mapping = dsl.get("categoryMapping", {})
            if category_mapping:
                category_ids = await self.build_category_hierarchy(category_mapping, domain)
                
                # 关联Skill到最细粒度的类目
                if category_ids:
                    await neo4j_client.execute_query("""
                        MATCH (sk:Skill {skill_id: $skill_id})
                        MATCH (c:Category {category_id: $category_id})
                        MERGE (sk)-[:BELONGS_TO_CATEGORY]->(c)
                    """, {
                        "skill_id": skill.skill_id,
                        "category_id": category_ids[-1]
                    })
            
            # 创建与Domain的关系
            await neo4j_client.execute_query("""
                MATCH (sk:Skill {skill_id: $skill_id})
                MATCH (d:Domain {domain_id: $domain_id})
                MERGE (sk)-[:BELONGS_TO_DOMAIN]->(d)
            """, {
                "skill_id": skill.skill_id,
                "domain_id": f"domain_{domain}"
            })
            
            logger.info(f"Skill同步到Neo4j成功: {skill.skill_id}")
            return result[0]["id"] if result else None
            
        except Exception as e:
            logger.error(f"Skill同步到Neo4j失败: {e}")
            return None
    
    async def get_3d_graph_data(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        domains: Optional[List[str]] = None,
        limit: int = 500
    ) -> Dict[str, Any]:
        """获取3D图谱可视化数据
        
        Args:
            start_year: 起始年份过滤
            end_year: 结束年份过滤
            domains: 领域过滤列表
            limit: 最大节点数
            
        Returns:
            包含nodes, edges, timeSlices, domains的数据
        """
        await self.initialize()
        
        try:
            # 构建过滤条件
            where_clauses = []
            params = {"limit": limit}
            
            if start_year:
                where_clauses.append("n.z >= $min_z")
                params["min_z"] = (start_year - BASE_YEAR) * Z_SCALE
            
            if end_year:
                where_clauses.append("n.z <= $max_z")
                params["max_z"] = (end_year - BASE_YEAR) * Z_SCALE
            
            if domains:
                where_clauses.append("n.domain IN $domains")
                params["domains"] = domains
            
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # 查询所有节点
            nodes_query = f"""
            MATCH (n)
            WHERE n:Standard OR n:Skill OR n:Category OR n:Domain OR n:TimeSlice
            {where_str if where_clauses else ''}
            RETURN 
                CASE 
                    WHEN n:Standard THEN n.standard_code
                    WHEN n:Skill THEN n.skill_id
                    WHEN n:Category THEN n.category_id
                    WHEN n:Domain THEN n.domain_id
                    WHEN n:TimeSlice THEN toString(n.year)
                END as id,
                labels(n)[0] as nodeType,
                properties(n) as properties
            LIMIT $limit
            """
            
            nodes_result = await neo4j_client.execute_query(nodes_query, params)
            
            # 查询所有关系
            edges_query = """
            MATCH (a)-[r]->(b)
            WHERE (a:Standard OR a:Skill OR a:Category OR a:Domain) 
              AND (b:Standard OR b:Skill OR b:Category OR b:Domain OR b:TimeSlice)
            RETURN 
                CASE 
                    WHEN a:Standard THEN a.standard_code
                    WHEN a:Skill THEN a.skill_id
                    WHEN a:Category THEN a.category_id
                    WHEN a:Domain THEN a.domain_id
                END as source,
                CASE 
                    WHEN b:Standard THEN b.standard_code
                    WHEN b:Skill THEN b.skill_id
                    WHEN b:Category THEN b.category_id
                    WHEN b:Domain THEN b.domain_id
                    WHEN b:TimeSlice THEN toString(b.year)
                END as target,
                type(r) as type
            LIMIT 1000
            """
            
            edges_result = await neo4j_client.execute_query(edges_query, {})
            
            # 查询时间切片
            time_slices_query = """
            MATCH (t:TimeSlice)
            RETURN t.year as year, t.z_position as z_position, t.label as label
            ORDER BY t.year
            """
            time_slices_result = await neo4j_client.execute_query(time_slices_query, {})
            
            # 查询领域列表
            domains_query = """
            MATCH (d:Domain)
            RETURN d.domain_id as domain_id, d.domain_name as domain_name, 
                   d.color as color, d.sector_angle as sector_angle
            ORDER BY d.sector_angle
            """
            domains_result = await neo4j_client.execute_query(domains_query, {})
            
            # 格式化节点数据
            nodes = []
            for record in nodes_result:
                props = record.get("properties", {})
                node = {
                    "id": record["id"],
                    "nodeType": record["nodeType"],
                    "label": props.get("standard_name") or props.get("skill_name") or 
                            props.get("category_name") or props.get("domain_name") or 
                            props.get("label") or record["id"],
                    "properties": props,
                    "position": {
                        "x": props.get("x", 0),
                        "y": props.get("y", 0),
                        "z": props.get("z", 0)
                    },
                    "style": {
                        "color": props.get("color", NODE_COLORS.get(record["nodeType"], "#666")),
                        "size": 10 if record["nodeType"] in ["Standard", "Skill"] else 8,
                        "opacity": 1.0
                    }
                }
                nodes.append(node)
            
            # 格式化边数据
            edges = []
            for record in edges_result:
                if record["source"] and record["target"]:
                    edges.append({
                        "source": record["source"],
                        "target": record["target"],
                        "type": record["type"]
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "timeSlices": time_slices_result,
                "domains": domains_result,
                "metadata": {
                    "totalNodes": len(nodes),
                    "totalEdges": len(edges),
                    "timeRange": {
                        "min": min([t["year"] for t in time_slices_result]) if time_slices_result else None,
                        "max": max([t["year"] for t in time_slices_result]) if time_slices_result else None
                    },
                    "domainCount": len(domains_result)
                }
            }
            
        except Exception as e:
            logger.error(f"获取3D图谱数据失败: {e}")
            # 返回空数据
            return {
                "nodes": [],
                "edges": [],
                "timeSlices": [],
                "domains": [],
                "metadata": {
                    "totalNodes": 0,
                    "totalEdges": 0,
                    "timeRange": {"min": None, "max": None},
                    "domainCount": 0
                }
            }
    
    async def get_domains(self) -> List[Dict[str, Any]]:
        """获取所有领域列表（优先从Neo4j获取，无数据时返回默认配置）"""
        try:
            query = """
            MATCH (d:Domain)
            RETURN d.domain_id as domain_id, d.domain_name as domain_name,
                   d.color as color, d.sector_angle as sector_angle
            ORDER BY d.sector_angle
            """
            result = await neo4j_client.execute_query(query, {})
            
            # 如果Neo4j没有数据，返回默认领域配置
            if not result:
                return [
                    {
                        "domain_id": f"domain_{k}",
                        "domain_name": v["name"],
                        "color": v["color"],
                        "sector_angle": v["sector_angle"]
                    }
                    for k, v in DEFAULT_DOMAIN_CONFIG.items()
                ]
            
            return result
        except Exception as e:
            logger.warning(f"获取领域列表失败: {e}")
            return [
                {
                    "domain_id": f"domain_{k}",
                    "domain_name": v["name"],
                    "color": v["color"],
                    "sector_angle": v["sector_angle"]
                }
                for k, v in DEFAULT_DOMAIN_CONFIG.items()
            ]
    
    async def get_time_slices(self) -> List[Dict[str, Any]]:
        """获取所有时间切片列表"""
        try:
            query = """
            MATCH (t:TimeSlice)
            RETURN t.year as year, t.z_position as z_position, t.label as label
            ORDER BY t.year
            """
            result = await neo4j_client.execute_query(query, {})
            
            # 如果没有数据，生成默认时间切片
            if not result:
                current_year = datetime.now().year
                return [
                    {
                        "year": year,
                        "z_position": (year - BASE_YEAR) * Z_SCALE,
                        "label": f"{year}年"
                    }
                    for year in range(2018, current_year + 1)
                ]
            
            return result
        except Exception as e:
            logger.warning(f"获取时间切片列表失败: {e}")
            current_year = datetime.now().year
            return [
                {
                    "year": year,
                    "z_position": (year - BASE_YEAR) * Z_SCALE,
                    "label": f"{year}年"
                }
                for year in range(2018, current_year + 1)
            ]
    
    async def sync_standard_series(self, series_code: str, series_name: str,
                                    domain_id: Optional[int] = None,
                                    part_count: int = 1) -> Optional[str]:
        """同步StandardSeries到Neo4j
        
        Args:
            series_code: 系列编号
            series_name: 系列名称
            domain_id: 领域ID
            part_count: 分部数量
            
        Returns:
            创建的节点ID，失败返回None
        """
        await self.initialize()
        
        try:
            query = """
            MERGE (ss:StandardSeries {series_code: $series_code})
            ON CREATE SET 
                ss.series_name = $series_name,
                ss.domain_id = $domain_id,
                ss.part_count = $part_count,
                ss.color = $color,
                ss.created_at = datetime()
            ON MATCH SET
                ss.series_name = $series_name,
                ss.part_count = $part_count,
                ss.updated_at = datetime()
            RETURN ss.series_code as id
            """
            
            result = await neo4j_client.execute_query(query, {
                "series_code": series_code,
                "series_name": series_name,
                "domain_id": domain_id,
                "part_count": part_count,
                "color": NODE_COLORS["StandardSeries"]
            })
            
            logger.info(f"StandardSeries同步到Neo4j成功: {series_code}")
            return result[0]["id"] if result else None
            
        except Exception as e:
            logger.error(f"StandardSeries同步到Neo4j失败: {e}")
            return None
    
    async def sync_skill_family(self, family_code: str, family_name: str,
                                 series_code: Optional[str] = None,
                                 domain_id: Optional[int] = None) -> Optional[str]:
        """同步SkillFamily到Neo4j
        
        Args:
            family_code: 技能族编码
            family_name: 技能族名称
            series_code: 关联的系列编号
            domain_id: 领域ID
            
        Returns:
            创建的节点ID，失败返回None
        """
        await self.initialize()
        
        try:
            query = """
            MERGE (sf:SkillFamily {family_code: $family_code})
            ON CREATE SET 
                sf.family_name = $family_name,
                sf.domain_id = $domain_id,
                sf.color = $color,
                sf.created_at = datetime()
            ON MATCH SET
                sf.family_name = $family_name,
                sf.updated_at = datetime()
            RETURN sf.family_code as id
            """
            
            result = await neo4j_client.execute_query(query, {
                "family_code": family_code,
                "family_name": family_name,
                "domain_id": domain_id,
                "color": NODE_COLORS["SkillFamily"]
            })
            
            # 如果有关联的系列，创建关系
            if series_code:
                await neo4j_client.execute_query("""
                    MATCH (sf:SkillFamily {family_code: $family_code})
                    MATCH (ss:StandardSeries {series_code: $series_code})
                    MERGE (sf)-[:FAMILY_FROM_SERIES]->(ss)
                """, {
                    "family_code": family_code,
                    "series_code": series_code
                })
            
            logger.info(f"SkillFamily同步到Neo4j成功: {family_code}")
            return result[0]["id"] if result else None
            
        except Exception as e:
            logger.error(f"SkillFamily同步到Neo4j失败: {e}")
            return None
    
    async def link_standard_to_series(self, standard_code: str, series_code: str) -> bool:
        """创建Standard与StandardSeries的关系
        
        Args:
            standard_code: 国标编号
            series_code: 系列编号
            
        Returns:
            是否成功
        """
        try:
            await neo4j_client.execute_query("""
                MATCH (s:Standard {standard_code: $standard_code})
                MATCH (ss:StandardSeries {series_code: $series_code})
                MERGE (s)-[:PART_OF_SERIES]->(ss)
            """, {
                "standard_code": standard_code,
                "series_code": series_code
            })
            return True
        except Exception as e:
            logger.warning(f"创建Standard-Series关系失败: {e}")
            return False
    
    async def link_skill_to_family(self, skill_id: str, family_code: str) -> bool:
        """创建Skill与SkillFamily的关系
        
        Args:
            skill_id: Skill ID
            family_code: 技能族编码
            
        Returns:
            是否成功
        """
        try:
            await neo4j_client.execute_query("""
                MATCH (sk:Skill {skill_id: $skill_id})
                MATCH (sf:SkillFamily {family_code: $family_code})
                MERGE (sk)-[:BELONGS_TO_FAMILY]->(sf)
            """, {
                "skill_id": skill_id,
                "family_code": family_code
            })
            return True
        except Exception as e:
            logger.warning(f"创建Skill-Family关系失败: {e}")
            return False


# 创建全局实例
kg_sync_service = KnowledgeGraphSyncService()
