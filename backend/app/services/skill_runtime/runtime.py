"""
GBSkillEngine Skill Runtime 执行引擎

负责执行Skill DSL，完成物料梳理
"""
import re
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill, SkillStatus
from app.models.execution_log import ExecutionLog
from app.schemas.material import (
    MaterialParseResponse,
    MaterialParseResult,
    ExecutionTrace,
    EngineExecutionStep,
    ParsedAttribute
)


class SkillRuntime:
    """Skill运行时引擎"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.trace_steps: List[EngineExecutionStep] = []
    
    async def execute(self, input_text: str, trace_id: str) -> MaterialParseResponse:
        """执行物料梳理"""
        start_time = time.time()
        self.trace_steps = []
        
        try:
            # 1. 意图解析和领域识别
            domain, intent_confidence = await self._intent_parsing(input_text)
            
            # 2. Skill路由
            skill = await self._skill_routing(input_text, domain)
            
            if not skill:
                # 使用默认处理
                result = await self._default_parse(input_text)
            else:
                # 3. 执行Skill
                result = await self._execute_skill(input_text, skill)
            
            # 计算总耗时
            total_duration = int((time.time() - start_time) * 1000)
            
            # 保存执行日志
            await self._save_execution_log(
                trace_id=trace_id,
                input_text=input_text,
                skill=skill,
                result=result,
                execution_time_ms=total_duration
            )
            
            return MaterialParseResponse(
                trace_id=trace_id,
                result=result,
                execution_trace=ExecutionTrace(
                    trace_id=trace_id,
                    steps=self.trace_steps,
                    total_duration_ms=total_duration
                ),
                matched_skill_id=skill.skill_id if skill else None
            )
            
        except Exception as e:
            # 记录错误
            total_duration = int((time.time() - start_time) * 1000)
            await self._save_execution_log(
                trace_id=trace_id,
                input_text=input_text,
                skill=None,
                result=None,
                execution_time_ms=total_duration,
                status="failed",
                error_message=str(e)
            )
            raise
    
    async def _intent_parsing(self, input_text: str) -> Tuple[str, float]:
        """意图解析 - 识别物料所属领域"""
        step_start = datetime.now()
        
        # 管材关键词
        pipe_patterns = [
            r"(UPVC|PVC|PE|PPR|管材|管道)",
            r"(DN|dn)\d+",
            r"(PN|pn)[\d.]+"
        ]
        
        # 紧固件关键词
        fastener_patterns = [
            r"(螺栓|螺钉|螺母|垫片)",
            r"M\d+",
            r"\d+\.\d+级"
        ]
        
        pipe_score = sum(1 for p in pipe_patterns if re.search(p, input_text, re.I))
        fastener_score = sum(1 for p in fastener_patterns if re.search(p, input_text, re.I))
        
        if pipe_score > fastener_score:
            domain = "pipe"
            confidence = min(0.9, 0.5 + pipe_score * 0.15)
        elif fastener_score > pipe_score:
            domain = "fastener"
            confidence = min(0.9, 0.5 + fastener_score * 0.15)
        else:
            domain = "general"
            confidence = 0.5
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="IntentParsing",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"input_text": input_text},
            output_data={"domain": domain, "confidence": confidence}
        ))
        
        return domain, confidence
    
    async def _skill_routing(self, input_text: str, domain: str) -> Optional[Skill]:
        """Skill路由 - 选择合适的Skill"""
        step_start = datetime.now()
        
        # 查找激活的Skill
        result = await self.db.execute(
            select(Skill)
            .where(Skill.domain == domain)
            .where(Skill.status == SkillStatus.ACTIVE)
            .order_by(Skill.priority.desc())
        )
        skills = result.scalars().all()
        
        # 如果没有激活的，查找所有可用的
        if not skills:
            result = await self.db.execute(
                select(Skill)
                .where(Skill.domain == domain)
                .order_by(Skill.priority.desc())
            )
            skills = result.scalars().all()
        
        selected_skill = skills[0] if skills else None
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="SkillRouter",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"domain": domain, "available_skills": len(skills)},
            output_data={
                "selected_skill": selected_skill.skill_id if selected_skill else None,
                "matched_count": len(skills)
            }
        ))
        
        return selected_skill
    
    async def _execute_skill(self, input_text: str, skill: Skill) -> MaterialParseResult:
        """执行Skill"""
        dsl = skill.dsl_content
        
        # 1. 属性抽取
        attributes = await self._extract_attributes(input_text, dsl)
        
        # 2. 规则映射
        attributes = await self._apply_rules(attributes, dsl)
        
        # 3. 表格查找
        attributes = await self._table_lookup(attributes, dsl)
        
        # 4. 类目映射
        category = await self._category_mapping(attributes, dsl)
        
        # 5. 构建结构化输出
        result = await self._build_struct(input_text, attributes, category, dsl)
        
        return result
    
    async def _extract_attributes(self, input_text: str, dsl: Dict) -> Dict[str, ParsedAttribute]:
        """属性抽取引擎"""
        step_start = datetime.now()
        attributes = {}
        
        attr_config = dsl.get("attributeExtraction", {})
        
        for attr_name, config in attr_config.items():
            patterns = config.get("patterns", [])
            value = None
            confidence = 0.0
            source = "default"
            
            # 尝试正则匹配
            for pattern in patterns:
                match = re.search(pattern, input_text, re.I)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    confidence = 0.9
                    source = "regex"
                    break
            
            # 使用默认值
            if value is None and "defaultValue" in config:
                value = config["defaultValue"]
                confidence = 0.5
                source = "default"
            
            if value is not None:
                # 类型转换
                if config.get("type") == "dimension" and value.isdigit():
                    value = int(value)
                
                attributes[attr_name] = ParsedAttribute(
                    value=value,
                    confidence=confidence,
                    source=source
                )
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="ExtractEngine",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"input_text": input_text},
            output_data={"attributes": {k: v.model_dump() for k, v in attributes.items()}}
        ))
        
        return attributes
    
    async def _apply_rules(self, attributes: Dict[str, ParsedAttribute], dsl: Dict) -> Dict[str, ParsedAttribute]:
        """规则引擎"""
        step_start = datetime.now()
        
        rules = dsl.get("rules", {})
        
        # 这里可以应用更复杂的规则逻辑
        # MVP版本简化处理
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="RuleEngine",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"rules_count": len(rules)},
            output_data={"applied_rules": []}
        ))
        
        return attributes
    
    async def _table_lookup(self, attributes: Dict[str, ParsedAttribute], dsl: Dict) -> Dict[str, ParsedAttribute]:
        """表格查找引擎"""
        step_start = datetime.now()
        tables = dsl.get("tables", {})
        found_values = {}
        
        # DN到外径的映射
        if "公称直径" in attributes and "dn_outer_diameter_map" in tables:
            dn_value = attributes["公称直径"].value
            table = tables["dn_outer_diameter_map"]
            
            for row in table.get("data", []):
                if len(row) >= 2 and row[0] == dn_value:
                    attributes["外径"] = ParsedAttribute(
                        value=row[1],
                        confidence=1.0,
                        source="table"
                    )
                    found_values["外径"] = row[1]
                    break
        
        # 尺寸表查找壁厚
        if "公称直径" in attributes and "公称压力" in attributes and "dimension_table" in tables:
            dn = attributes["公称直径"].value
            pn = attributes["公称压力"].value
            table = tables["dimension_table"]
            columns = table.get("columns", [])
            
            # 查找PN对应的列索引
            pn_col = None
            for i, col in enumerate(columns):
                if f"PN{pn}" in col or f"pn{pn}" in col.lower():
                    pn_col = i
                    break
            
            if pn_col:
                for row in table.get("data", []):
                    if row[0] == dn and len(row) > pn_col:
                        attributes["壁厚"] = ParsedAttribute(
                            value=row[pn_col],
                            confidence=1.0,
                            source="table"
                        )
                        found_values["壁厚"] = row[pn_col]
                        break
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="TableEngine",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"tables_count": len(tables)},
            output_data={"found_values": found_values}
        ))
        
        return attributes
    
    async def _category_mapping(self, attributes: Dict[str, ParsedAttribute], dsl: Dict) -> Dict[str, str]:
        """类目映射引擎"""
        step_start = datetime.now()
        
        category_config = dsl.get("categoryMapping", {})
        
        category = {
            "primaryCategory": category_config.get("primaryCategory", "未分类"),
            "secondaryCategory": category_config.get("secondaryCategory", ""),
            "tertiaryCategory": category_config.get("tertiaryCategory", ""),
            "categoryId": category_config.get("categoryId", "")
        }
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="CategoryEngine",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={},
            output_data={"category": category}
        ))
        
        return category
    
    async def _build_struct(
        self,
        input_text: str,
        attributes: Dict[str, ParsedAttribute],
        category: Dict[str, str],
        dsl: Dict
    ) -> MaterialParseResult:
        """结构化输出构建器"""
        step_start = datetime.now()
        
        # 计算整体置信度
        if attributes:
            confidence_score = sum(a.confidence for a in attributes.values()) / len(attributes)
        else:
            confidence_score = 0.5
        
        # 构建物料名称
        material_parts = []
        if "材质" in attributes:
            material_parts.append(str(attributes["材质"].value))
        material_parts.append("管" if dsl.get("domain") == "pipe" else "件")
        if "公称直径" in attributes:
            material_parts.append(f"DN{attributes['公称直径'].value}")
        
        material_name = "".join(material_parts) if material_parts else input_text[:20]
        
        result = MaterialParseResult(
            material_name=material_name,
            category=category,
            attributes=attributes,
            standard_code=dsl.get("standardCode"),
            confidence_score=round(confidence_score, 3)
        )
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="StructBuilder",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={},
            output_data={"material_name": material_name, "confidence": confidence_score}
        ))
        
        return result
    
    async def _default_parse(self, input_text: str) -> MaterialParseResult:
        """默认解析（无匹配Skill时）"""
        return MaterialParseResult(
            material_name=input_text[:50],
            category={
                "primaryCategory": "未分类",
                "secondaryCategory": "",
                "tertiaryCategory": "",
                "categoryId": ""
            },
            attributes={},
            standard_code=None,
            confidence_score=0.3
        )
    
    async def _save_execution_log(
        self,
        trace_id: str,
        input_text: str,
        skill: Optional[Skill],
        result: Optional[MaterialParseResult],
        execution_time_ms: int,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """保存执行日志"""
        log = ExecutionLog(
            trace_id=trace_id,
            input_text=input_text,
            matched_skills=[skill.skill_id] if skill else [],
            executed_skill_id=skill.skill_id if skill else None,
            execution_trace={
                "steps": [s.model_dump(mode='json') for s in self.trace_steps]
            },
            output_result=result.model_dump(mode='json') if result else None,
            confidence_score=result.confidence_score if result else None,
            execution_time_ms=execution_time_ms,
            status=status,
            error_message=error_message
        )
        
        self.db.add(log)
        await self.db.commit()
