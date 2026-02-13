"""
GBSkillEngine Skill Runtime 执行引擎

负责执行Skill DSL，完成物料梳理
"""
import re
import time
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
            # 1. 加载所有可用Skill进行意图匹配
            skill, intent_confidence = await self._match_skill(input_text)
            
            if not skill:
                # 使用默认处理
                result = await self._default_parse(input_text)
            else:
                # 2. 执行Skill
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
    
    async def _match_skill(self, input_text: str) -> Tuple[Optional[Skill], float]:
        """基于意图识别匹配最佳Skill"""
        step_start = datetime.now()
        
        # 获取所有激活的Skill
        result = await self.db.execute(
            select(Skill).where(Skill.status == SkillStatus.ACTIVE).order_by(Skill.priority.desc())
        )
        active_skills = result.scalars().all()
        
        # 如果没有激活的，获取所有Skill
        if not active_skills:
            result = await self.db.execute(
                select(Skill).order_by(Skill.priority.desc())
            )
            active_skills = result.scalars().all()
        
        best_skill = None
        best_score = 0.0
        match_details = {}
        
        for skill in active_skills:
            score = self._calculate_intent_score(input_text, skill)
            match_details[skill.skill_id] = score
            
            if score > best_score:
                best_score = score
                best_skill = skill
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="IntentMatching",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"input_text": input_text, "available_skills": len(active_skills)},
            output_data={
                "matched_skill": best_skill.skill_id if best_skill else None,
                "confidence": best_score,
                "all_scores": match_details
            }
        ))
        
        return best_skill, best_score
    
    def _calculate_intent_score(self, input_text: str, skill: Skill) -> float:
        """计算输入文本与Skill的匹配度"""
        dsl = skill.dsl_content
        intent = dsl.get("intentRecognition", {})
        
        keywords = intent.get("keywords", [])
        patterns = intent.get("patterns", [])
        
        score = 0.0
        max_score = max(len(keywords) + len(patterns), 1)
        
        # 关键词匹配
        for kw in keywords:
            if kw.lower() in input_text.lower():
                score += 1.0
        
        # 正则模式匹配（权重更高）
        for pattern in patterns:
            try:
                if re.search(pattern, input_text, re.I):
                    score += 1.5
            except re.error:
                continue
        
        return min(score / max_score, 1.0)
    
    async def _execute_skill(self, input_text: str, skill: Skill) -> MaterialParseResult:
        """执行Skill"""
        dsl = skill.dsl_content
        
        # 1. 属性抽取
        attributes = await self._extract_attributes(input_text, dsl)
        
        # 2. 表格查找（增强版）
        attributes = await self._enhanced_table_lookup(attributes, dsl)
        
        # 3. 规则映射
        attributes = await self._apply_rules(attributes, dsl)
        
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
                try:
                    match = re.search(pattern, input_text, re.I)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
                        confidence = 0.9
                        source = "regex"
                        break
                except re.error:
                    continue
            
            # 使用默认值
            if value is None and "defaultValue" in config:
                value = config["defaultValue"]
                confidence = 0.5
                source = "default"
            
            if value is not None:
                # 类型转换
                if config.get("type") == "dimension":
                    try:
                        # 尝试转换为数字
                        if isinstance(value, str) and value.replace(".", "").isdigit():
                            value = float(value) if "." in value else int(value)
                    except (ValueError, TypeError):
                        pass
                
                attributes[attr_name] = ParsedAttribute(
                    value=value,
                    confidence=confidence,
                    source=source,
                    unit=config.get("unit", ""),
                    displayName=config.get("displayName", attr_name),
                    description=config.get("description", "")
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
    
    async def _enhanced_table_lookup(
        self, 
        attributes: Dict[str, ParsedAttribute], 
        dsl: Dict
    ) -> Dict[str, ParsedAttribute]:
        """增强版表格查找引擎"""
        step_start = datetime.now()
        tables = dsl.get("tables", {})
        found_values = {}
        
        # 获取DN值
        dn_value = None
        if "公称直径" in attributes:
            dn_value = attributes["公称直径"].value
            if isinstance(dn_value, str):
                try:
                    dn_value = int(dn_value)
                except ValueError:
                    pass
        
        # 获取PN值
        pn_value = None
        if "公称压力" in attributes:
            pn_value = attributes["公称压力"].value
            if isinstance(pn_value, str):
                try:
                    pn_value = float(pn_value)
                except ValueError:
                    pass
        
        # 1. DN → 公称外径查找
        if dn_value and "dn_outer_diameter_map" in tables:
            table = tables["dn_outer_diameter_map"]
            for row in table.get("data", []):
                if len(row) >= 2 and row[0] == dn_value:
                    od_value = row[1]
                    attributes["公称外径"] = ParsedAttribute(
                        value=od_value,
                        confidence=1.0,
                        source="table",
                        unit="mm",
                        displayName="公称外径Φ(mm)",
                        description=f"表2规定DN{dn_value}对应的公称外径d_n为{od_value}mm"
                    )
                    found_values["公称外径"] = od_value
                    break
        
        # 2. PN → 管系列S查找
        series_value = None
        if pn_value and "series_mapping" in tables:
            table = tables["series_mapping"]
            for row in table.get("data", []):
                if len(row) >= 2 and row[0] == pn_value:
                    series_value = row[1]
                    design_coeff = row[2] if len(row) > 2 else 2.0
                    attributes["管系列"] = ParsedAttribute(
                        value=series_value,
                        confidence=1.0,
                        source="table",
                        unit="",
                        displayName="管系列(S)",
                        description=f"附录B显示当设计系数C={design_coeff}时，PN{pn_value}对应{series_value}系列"
                    )
                    found_values["管系列"] = series_value
                    break
        
        # 3. 外径 + 管系列 → 最小壁厚查找
        od_value = found_values.get("公称外径") or (
            attributes.get("公称外径").value if "公称外径" in attributes else None
        )
        
        if od_value and series_value and "dimension_table" in tables:
            table = tables["dimension_table"]
            columns = table.get("columns", [])
            
            # 查找系列对应的列索引
            series_col = None
            for i, col in enumerate(columns):
                if series_value in col:
                    series_col = i
                    break
            
            if series_col is not None:
                for row in table.get("data", []):
                    if len(row) > series_col and row[0] == od_value:
                        wall_thickness = row[series_col]
                        attributes["最小壁厚"] = ParsedAttribute(
                            value=wall_thickness,
                            confidence=1.0,
                            source="table",
                            unit="mm",
                            displayName=f"最小壁厚(e_min)",
                            description=f"表1规定外径{od_value}mm且为{series_value}系列时，最小壁厚为{wall_thickness}mm"
                        )
                        found_values["最小壁厚"] = wall_thickness
                        
                        # 查找壁厚偏差
                        if "wall_thickness_tolerance" in tables:
                            tolerance = self._lookup_wall_thickness_tolerance(
                                wall_thickness, 
                                tables["wall_thickness_tolerance"]
                            )
                            if tolerance is not None:
                                attributes["壁厚偏差"] = ParsedAttribute(
                                    value=f"+{tolerance}",
                                    confidence=1.0,
                                    source="table",
                                    unit="mm",
                                    displayName="壁厚偏差",
                                    description=f"表1规定外径{od_value}mm且为{series_value}系列时，壁厚正偏差为{tolerance}mm"
                                )
                                found_values["壁厚偏差"] = tolerance
                        break
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="TableEngine",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"tables_count": len(tables), "dn": dn_value, "pn": pn_value},
            output_data={"found_values": found_values}
        ))
        
        return attributes
    
    def _lookup_wall_thickness_tolerance(
        self, 
        wall_thickness: float, 
        tolerance_table: Dict
    ) -> Optional[float]:
        """查找壁厚偏差"""
        for row in tolerance_table.get("data", []):
            if len(row) >= 2:
                range_str = str(row[0])
                tolerance = row[1]
                
                # 解析范围 "6.1-10.0"
                if "-" in range_str:
                    parts = range_str.split("-")
                    if len(parts) == 2:
                        try:
                            min_val = float(parts[0])
                            max_val = float(parts[1])
                            if min_val <= wall_thickness <= max_val:
                                return tolerance
                        except ValueError:
                            continue
        return None
    
    async def _apply_rules(
        self, 
        attributes: Dict[str, ParsedAttribute], 
        dsl: Dict
    ) -> Dict[str, ParsedAttribute]:
        """规则引擎"""
        step_start = datetime.now()
        
        rules = dsl.get("rules", {})
        applied_rules = []
        
        # 应用规则逻辑
        # 例如：根据材质推断管件材质描述
        if "材质" in attributes:
            material = attributes["材质"].value
            material_desc_map = {
                "UPVC": "硬聚氯乙烯(PVC)",
                "PVC-U": "硬聚氯乙烯(PVC)",
                "PVC": "聚氯乙烯(PVC)",
                "PE": "聚乙烯(PE)",
                "PPR": "无规共聚聚丙烯(PP-R)",
            }
            if material in material_desc_map:
                attributes["管件材质"] = ParsedAttribute(
                    value=material_desc_map[material],
                    confidence=1.0,
                    source="rule",
                    unit="",
                    displayName="管件材质",
                    description=f"以聚氯乙烯(PVC)树脂为主要原料的混配料"
                )
                applied_rules.append(f"material_desc:{material}")
        
        step_end = datetime.now()
        self.trace_steps.append(EngineExecutionStep(
            engine="RuleEngine",
            start_time=step_start,
            end_time=step_end,
            duration_ms=int((step_end - step_start).total_seconds() * 1000),
            input_data={"rules_count": len(rules)},
            output_data={"applied_rules": applied_rules}
        ))
        
        return attributes
    
    async def _category_mapping(
        self, 
        attributes: Dict[str, ParsedAttribute], 
        dsl: Dict
    ) -> Dict[str, str]:
        """类目映射引擎"""
        step_start = datetime.now()
        
        category_config = dsl.get("categoryMapping", {})
        
        category = {
            "primaryCategory": category_config.get("primaryCategory", "未分类"),
            "secondaryCategory": category_config.get("secondaryCategory", ""),
            "tertiaryCategory": category_config.get("tertiaryCategory", ""),
            "quaternaryCategory": category_config.get("quaternaryCategory", ""),
            "categoryId": category_config.get("categoryId", ""),
            "commonName": category_config.get("commonName", "")
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
        
        # 使用通用名称（如果有）
        common_name = category.get("commonName", "")
        if not common_name and "材质" in attributes:
            common_name = f"工业用{attributes['材质'].value}管材"
        
        result = MaterialParseResult(
            material_name=material_name,
            common_name=common_name,
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
            common_name="",
            category={
                "primaryCategory": "未分类",
                "secondaryCategory": "",
                "tertiaryCategory": "",
                "quaternaryCategory": "",
                "categoryId": "",
                "commonName": ""
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
