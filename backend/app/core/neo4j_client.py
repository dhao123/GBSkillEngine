"""
GBSkillEngine Neo4j 客户端
"""
from neo4j import AsyncGraphDatabase
from typing import Optional, List, Dict, Any
from app.config import settings


class Neo4jClient:
    """Neo4j 异步客户端封装"""
    
    _driver = None
    
    @classmethod
    async def get_driver(cls):
        """获取Neo4j驱动"""
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return cls._driver
    
    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
    
    @classmethod
    async def execute_query(
        cls,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        driver = await cls.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
    
    @classmethod
    async def create_node(
        cls,
        label: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建节点"""
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
        result = await cls.execute_query(query, properties)
        return result[0]["n"] if result else {}
    
    @classmethod
    async def create_relationship(
        cls,
        from_label: str,
        from_props: Dict[str, Any],
        to_label: str,
        to_props: Dict[str, Any],
        rel_type: str,
        rel_props: Optional[Dict[str, Any]] = None
    ) -> bool:
        """创建关系"""
        from_match = " AND ".join([f"a.{k} = $from_{k}" for k in from_props.keys()])
        to_match = " AND ".join([f"b.{k} = $to_{k}" for k in to_props.keys()])
        
        params = {f"from_{k}": v for k, v in from_props.items()}
        params.update({f"to_{k}": v for k, v in to_props.items()})
        
        rel_str = ""
        if rel_props:
            rel_str = " {" + ", ".join([f"{k}: $rel_{k}" for k in rel_props.keys()]) + "}"
            params.update({f"rel_{k}": v for k, v in rel_props.items()})
        
        query = f"""
        MATCH (a:{from_label}), (b:{to_label})
        WHERE {from_match} AND {to_match}
        CREATE (a)-[r:{rel_type}{rel_str}]->(b)
        RETURN r
        """
        result = await cls.execute_query(query, params)
        return len(result) > 0
    
    @classmethod
    async def get_graph_data(
        cls,
        center_node_id: Optional[str] = None,
        depth: int = 2
    ) -> Dict[str, Any]:
        """获取图谱可视化数据"""
        if center_node_id:
            query = f"""
            MATCH path = (n)-[*0..{depth}]-(m)
            WHERE id(n) = $node_id
            RETURN path
            """
            params = {"node_id": int(center_node_id)}
        else:
            query = f"""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 100
            """
            params = {}
        
        records = await cls.execute_query(query, params)
        
        nodes = {}
        edges = []
        
        for record in records:
            if "n" in record and record["n"]:
                node = record["n"]
                node_id = str(node.get("id", id(node)))
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": list(node.labels)[0] if hasattr(node, 'labels') else "Node",
                        "properties": dict(node)
                    }
            
            if "m" in record and record["m"]:
                node = record["m"]
                node_id = str(node.get("id", id(node)))
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": list(node.labels)[0] if hasattr(node, 'labels') else "Node",
                        "properties": dict(node)
                    }
            
            if "r" in record and record["r"]:
                rel = record["r"]
                edges.append({
                    "source": str(rel.start_node.get("id", "")),
                    "target": str(rel.end_node.get("id", "")),
                    "type": rel.type
                })
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }


# 便捷函数
neo4j_client = Neo4jClient()
