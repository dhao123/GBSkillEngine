"""
GBSkillEngine LLM Skill编译器

使用LLM将国标文档编译为Skill DSL
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
import re
import os

from app.models.standard import Standard
from app.models.skill import Skill, SkillStatus
from app.services.llm.base import BaseLLMProvider, LLMError
from app.services.llm.factory import get_default_provider
from app.services.document_parser import parse_standard_document, ParsedDocument
from app.services.skill_compiler.prompts import (
    SYSTEM_PROMPT,
    DOMAIN_DETECTION_PROMPT,
    ATTRIBUTE_EXTRACTION_PROMPT,
    INTENT_RECOGNITION_PROMPT,
    CATEGORY_MAPPING_PROMPT,
    TABLE_EXTRACTION_PROMPT,
)
from app.config import settings

logger = logging.getLogger(__name__)


class LLMSkillCompiler:
    """LLM驱动的Skill编译器"""
    
    def __init__(self, db: AsyncSession, llm_provider: Optional[BaseLLMProvider] = None):
        self.db = db
        self._llm_provider = llm_provider
        self._parsed_doc: Optional[ParsedDocument] = None
    
    async def _get_provider(self) -> BaseLLMProvider:
        """获取LLM Provider"""
        if self._llm_provider:
            return self._llm_provider
        
        provider = await get_default_provider(self.db)
        if not provider:
            raise LLMError(
                message="未配置LLM Provider，请先在系统配置中添加LLM配置",
                provider="none"
            )
        return provider
    
    def _generate_skill_id(self, standard: Standard) -> str:
        """生成Skill ID"""
        code = standard.standard_code.replace("/", "_").replace(".", "_").replace("-", "_").lower()
        return f"skill_{code}"
    
    def _parse_document(self, standard: Standard) -> Optional[ParsedDocument]:
        """解析国标文档"""
        if not standard.file_path or not os.path.exists(standard.file_path):
            logger.warning(f"国标文档不存在: {standard.file_path}")
            return None
        
        try:
            return parse_standard_document(standard.file_path)
        except Exception as e:
            logger.warning(f"文档解析失败: {e}")
            return None
    
    async def compile(self, standard: Standard) -> Skill:
        """
        编译国标为Skill
        
        Args:
            standard: 国标模型实例
            
        Returns:
            生成的Skill实例
        """
        logger.info(f"开始LLM编译: {standard.standard_code}")
        
        provider = await self._get_provider()
        
        # Step 0: 解析文档获取内容
        self._parsed_doc = self._parse_document(standard)
        if self._parsed_doc:
            logger.info(f"文档解析成功，提取到 {len(self._parsed_doc.sections)} 个章节, {len(self._parsed_doc.tables)} 个表格")
        
        # Step 1: 检测领域
        domain = await self._detect_domain(provider, standard)
        logger.debug(f"检测到领域: {domain}")
        
        # Step 2: 提取属性定义
        attributes = await self._extract_attributes(provider, standard, domain)
        logger.debug(f"提取到 {len(attributes)} 个属性")
        
        # Step 3: 生成意图识别规则
        intent = await self._generate_intent(provider, standard, domain, attributes)
        
        # Step 4: 生成类目映射
        category = await self._generate_category(provider, standard, domain)
        
        # Step 5: 提取表格数据
        tables = await self._extract_tables(provider, standard, domain)
        
        # Step 6: 组装完整DSL
        dsl = self._assemble_dsl(standard, domain, attributes, intent, category, tables)
        
        # Step 7: 验证DSL
        self._validate_dsl(dsl)
        
        # Step 8: 创建Skill记录
        skill_id = self._generate_skill_id(standard)
        
        skill = Skill(
            skill_id=skill_id,
            skill_name=dsl["skillName"],
            standard_id=standard.id,
            domain=domain,
            priority=dsl.get("priority", 100),
            applicable_material_types=dsl.get("applicableMaterialTypes", []),
            dsl_content=dsl,
            dsl_version="1.0.0",
            status=SkillStatus.DRAFT
        )
        
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        
        logger.info(f"LLM编译完成: {skill.skill_id}")
        
        return skill
    
    def _get_document_content(self, max_length: int = 8000) -> str:
        """获取文档内容摘要"""
        if not self._parsed_doc:
            return "文档内容不可用"
        
        content = self._parsed_doc.text[:max_length]
        if len(self._parsed_doc.text) > max_length:
            content += "\n... (文档内容过长，已截断)"
        
        return content
    
    def _get_document_summary(self, standard: Standard) -> str:
        """获取文档摘要"""
        parts = []
        
        if standard.product_scope:
            parts.append(f"产品范围: {standard.product_scope}")
        
        # 使用解析后的文档内容
        if self._parsed_doc:
            if self._parsed_doc.title:
                parts.append(f"文档标题: {self._parsed_doc.title}")
            
            if self._parsed_doc.sections:
                section_titles = [f"{s['number']} {s['title']}" for s in self._parsed_doc.sections[:10]]
                parts.append(f"主要章节: {', '.join(section_titles)}")
            
            if self._parsed_doc.tables:
                table_info = [t.get('title', t.get('table_id', '')) for t in self._parsed_doc.tables[:5]]
                parts.append(f"包含表格: {', '.join(table_info)}")
            
            # 添加文档正文摘要（前2000字符）
            if self._parsed_doc.text:
                parts.append(f"文档内容摘要:\n{self._parsed_doc.text[:2000]}")
        
        return "\n".join(parts) if parts else "无文档摘要"
    
    async def _detect_domain(self, provider: BaseLLMProvider, standard: Standard) -> str:
        """检测国标领域"""
        prompt = DOMAIN_DETECTION_PROMPT.format(
            standard_code=standard.standard_code,
            standard_name=standard.standard_name,
            product_scope=standard.product_scope or "未指定"
        )
        
        try:
            result = await provider.generate_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
            return result.get("domain", "general")
        except Exception as e:
            logger.warning(f"领域检测失败，使用规则检测: {e}")
            return self._detect_domain_by_rules(standard)
    
    def _detect_domain_by_rules(self, standard: Standard) -> str:
        """基于规则的领域检测（回退方案）"""
        code = standard.standard_code.lower()
        name = standard.standard_name.lower()
        text = f"{code} {name}"
        
        domain_rules = {
            "pipe": ["管", "管道", "管材", "pvc", "pe", "ppr", "4219"],
            "fastener": ["螺栓", "螺钉", "螺母", "紧固", "5782", "5783"],
            "valve": ["阀", "闸阀", "球阀", "蝶阀"],
            "fitting": ["管件", "弯头", "三通", "法兰"],
            "cable": ["电缆", "电线", "导线"],
            "bearing": ["轴承"],
            "seal": ["密封", "垫片", "o型圈"],
        }
        
        for domain, keywords in domain_rules.items():
            if any(kw in text for kw in keywords):
                return domain
        
        return "general"
    
    async def _extract_attributes(
        self, 
        provider: BaseLLMProvider, 
        standard: Standard, 
        domain: str
    ) -> Dict[str, Any]:
        """提取属性定义"""
        prompt = ATTRIBUTE_EXTRACTION_PROMPT.format(
            standard_code=standard.standard_code,
            standard_name=standard.standard_name,
            domain=domain,
            product_scope=standard.product_scope or "未指定",
            document_content=self._get_document_content(6000)
        )
        
        try:
            return await provider.generate_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
        except Exception as e:
            logger.warning(f"属性提取失败，使用默认属性: {e}")
            return self._get_default_attributes(domain)
    
    async def _generate_intent(
        self,
        provider: BaseLLMProvider,
        standard: Standard,
        domain: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成意图识别规则"""
        prompt = INTENT_RECOGNITION_PROMPT.format(
            standard_code=standard.standard_code,
            standard_name=standard.standard_name,
            domain=domain,
            product_scope=standard.product_scope or "未指定",
            attributes=json.dumps(list(attributes.keys()), ensure_ascii=False)
        )
        
        try:
            return await provider.generate_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
        except Exception as e:
            logger.warning(f"意图识别生成失败，使用默认规则: {e}")
            return self._get_default_intent(domain)
    
    async def _generate_category(
        self,
        provider: BaseLLMProvider,
        standard: Standard,
        domain: str
    ) -> Dict[str, Any]:
        """生成类目映射"""
        prompt = CATEGORY_MAPPING_PROMPT.format(
            standard_code=standard.standard_code,
            standard_name=standard.standard_name,
            domain=domain,
            product_scope=standard.product_scope or "未指定"
        )
        
        try:
            return await provider.generate_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
        except Exception as e:
            logger.warning(f"类目映射生成失败，使用默认类目: {e}")
            return self._get_default_category(domain)
    
    async def _extract_tables(
        self,
        provider: BaseLLMProvider,
        standard: Standard,
        domain: str
    ) -> Dict[str, Any]:
        """提取表格数据（用于尺寸查找）"""
        # 构建表格提取提示
        prompt = TABLE_EXTRACTION_PROMPT.format(
            standard_code=standard.standard_code,
            standard_name=standard.standard_name,
            domain=domain,
            document_content=self._get_document_content(8000)
        )
        
        try:
            result = await provider.generate_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
            return result
        except Exception as e:
            logger.warning(f"表格提取失败，使用默认表格: {e}")
            return self._get_default_tables(domain)
    
    def _assemble_dsl(
        self,
        standard: Standard,
        domain: str,
        attributes: Dict[str, Any],
        intent: Dict[str, Any],
        category: Dict[str, Any],
        tables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """组装完整的DSL"""
        skill_id = self._generate_skill_id(standard)
        
        dsl = {
            "skillId": skill_id,
            "skillName": f"{standard.standard_name} Skill",
            "version": "1.0.0",
            "standardCode": standard.standard_code,
            "domain": domain,
            "applicableMaterialTypes": self._infer_material_types(domain, standard),
            "priority": 100,
            "intentRecognition": intent,
            "attributeExtraction": attributes,
            "tables": tables,
            "categoryMapping": category,
            "outputStructure": self._generate_output_structure(attributes, category),
            "fallbackStrategy": {
                "lowConfidenceThreshold": 0.6,
                "humanReviewRequired": True
            }
        }
        
        return dsl
    
    def _validate_dsl(self, dsl: Dict[str, Any]) -> bool:
        """验证DSL结构"""
        required_fields = ["skillId", "skillName", "domain", "attributeExtraction"]
        
        for field in required_fields:
            if field not in dsl:
                raise ValueError(f"DSL缺少必填字段: {field}")
        
        # 验证正则表达式语法
        for attr_name, attr_def in dsl.get("attributeExtraction", {}).items():
            patterns = attr_def.get("patterns", [])
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    logger.warning(f"属性 {attr_name} 的正则表达式无效: {pattern}, 错误: {e}")
        
        return True
    
    def _get_default_attributes(self, domain: str) -> Dict[str, Any]:
        """获取默认属性定义"""
        defaults = {
            "pipe": {
                "公称直径": {
                    "type": "dimension",
                    "unit": "mm",
                    "patterns": ["DN(\\d+)", "dn(\\d+)", "直径(\\d+)"],
                    "required": True,
                    "displayName": "公称直径(DN)"
                },
                "公称压力": {
                    "type": "dimension",
                    "unit": "MPa",
                    "patterns": ["PN([\\d.]+)", "pn([\\d.]+)"],
                    "required": False,
                    "displayName": "公称压力(PN)"
                },
                "材质": {
                    "type": "material",
                    "patterns": ["(UPVC|PVC-U|PVC|PE|PPR|PP-R|硬聚氯乙烯)"],
                    "required": False,
                    "defaultValue": "PVC-U",
                    "displayName": "管件材质"
                }
            },
            "fastener": {
                "规格": {
                    "type": "specification",
                    "patterns": ["M(\\d+)[×xX](\\d+)", "M(\\d+)"],
                    "required": True,
                    "displayName": "规格"
                },
                "材质": {
                    "type": "material",
                    "patterns": ["(碳钢|不锈钢|304|316|Q235)"],
                    "required": False,
                    "defaultValue": "碳钢",
                    "displayName": "材质"
                },
                "性能等级": {
                    "type": "performance",
                    "patterns": ["([\\d.]+)级", "等级([\\d.]+)"],
                    "allowedValues": ["4.8", "8.8", "10.9", "12.9"],
                    "required": False,
                    "displayName": "性能等级"
                }
            }
        }
        
        return defaults.get(domain, {
            "规格型号": {
                "type": "specification",
                "patterns": ["([A-Za-z0-9-]+)"],
                "required": True,
                "displayName": "规格型号"
            }
        })
    
    def _get_default_intent(self, domain: str) -> Dict[str, Any]:
        """获取默认意图识别规则"""
        defaults = {
            "pipe": {
                "keywords": ["管", "管材", "管道", "DN", "PN", "UPVC", "PVC", "PE", "PPR", "硬聚氯乙烯"],
                "patterns": ["(DN|dn)\\d+", "(PN|pn)[\\d.]+", "UPVC|PVC-U|PVC|PE|PPR"]
            },
            "fastener": {
                "keywords": ["螺栓", "螺钉", "螺母", "垫片", "M6", "M8", "M10", "M12"],
                "patterns": ["M\\d+[×xX]?\\d*", "螺栓|螺钉|螺母"]
            }
        }
        
        return defaults.get(domain, {
            "keywords": [],
            "patterns": []
        })
    
    def _get_default_category(self, domain: str) -> Dict[str, Any]:
        """获取默认类目映射"""
        defaults = {
            "pipe": {
                "primaryCategory": "管道系统",
                "secondaryCategory": "工业用塑料管道",
                "tertiaryCategory": "硬聚氯乙烯(PVC-U)",
                "quaternaryCategory": "工业用PVC-U管材",
                "categoryId": "CAT_PIPE_001"
            },
            "fastener": {
                "primaryCategory": "紧固件",
                "secondaryCategory": "螺栓",
                "tertiaryCategory": "六角头螺栓",
                "quaternaryCategory": "",
                "categoryId": "CAT_FASTENER_001"
            }
        }
        
        return defaults.get(domain, {
            "primaryCategory": "通用",
            "secondaryCategory": "其他",
            "tertiaryCategory": "未分类",
            "quaternaryCategory": "",
            "categoryId": "CAT_GENERAL_001"
        })
    
    def _get_default_tables(self, domain: str) -> Dict[str, Any]:
        """获取默认表格数据"""
        if domain == "pipe":
            return {
                "dn_outer_diameter_map": {
                    "description": "公称直径DN到公称外径的映射表",
                    "source": "GB/T 4219.1 表2",
                    "columns": ["DN", "公称外径(mm)"],
                    "data": [
                        [10, 16], [15, 20], [20, 25], [25, 32], [32, 40],
                        [40, 50], [50, 63], [65, 75], [80, 90], [100, 110],
                        [125, 140], [150, 160], [200, 225], [250, 280],
                        [300, 315], [350, 355], [400, 400], [450, 450],
                        [500, 500], [600, 630]
                    ]
                },
                "series_mapping": {
                    "description": "PN等级到管系列S的映射",
                    "source": "GB/T 4219.1 附录B",
                    "columns": ["PN", "管系列S", "设计系数C"],
                    "data": [
                        [0.6, "S20", 2.0],
                        [0.8, "S16", 2.0],
                        [1.0, "S12.5", 2.0],
                        [1.25, "S10", 2.0],
                        [1.6, "S8", 2.0],
                        [2.0, "S6.3", 2.0],
                        [2.5, "S5", 2.0]
                    ]
                },
                "dimension_table": {
                    "description": "管材尺寸表 - 外径与壁厚对应关系",
                    "source": "GB/T 4219.1 表1",
                    "columns": ["公称外径(mm)", "S20壁厚", "S16壁厚", "S12.5壁厚", "S10壁厚", "S8壁厚", "S6.3壁厚", "S5壁厚"],
                    "data": [
                        [16, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.5],
                        [20, 1.0, 1.0, 1.0, 1.0, 1.2, 1.5, 1.9],
                        [25, 1.0, 1.0, 1.0, 1.2, 1.5, 1.9, 2.3],
                        [32, 1.0, 1.0, 1.2, 1.6, 1.9, 2.4, 3.0],
                        [40, 1.0, 1.2, 1.5, 1.9, 2.4, 3.0, 3.7],
                        [50, 1.2, 1.5, 1.9, 2.4, 3.0, 3.7, 4.6],
                        [63, 1.5, 1.9, 2.4, 3.0, 3.8, 4.7, 5.8],
                        [75, 1.8, 2.2, 2.9, 3.6, 4.5, 5.6, 6.9],
                        [90, 2.2, 2.7, 3.5, 4.3, 5.4, 6.7, 8.2],
                        [110, 2.7, 3.4, 4.2, 5.3, 6.6, 8.2, 10.0],
                        [140, 3.4, 4.3, 5.4, 6.7, 8.3, 10.3, 12.7],
                        [160, 3.9, 4.9, 6.2, 7.7, 9.5, 11.8, 14.6],
                        [225, 5.5, 6.9, 8.6, 10.8, 13.4, 16.6, 20.5],
                        [280, 6.9, 8.6, 10.7, 13.4, 16.6, 20.6, 25.4],
                        [315, 7.7, 9.7, 12.1, 15.0, 18.7, 23.2, 28.6],
                        [355, 8.7, 10.9, 13.6, 16.9, 21.1, 26.1, 32.2],
                        [400, 9.8, 12.3, 15.3, 19.1, 23.7, 29.4, 36.3],
                        [450, 11.0, 13.8, 17.2, 21.5, 26.7, 33.1, 40.9],
                        [500, 12.3, 15.3, 19.1, 23.9, 29.7, 36.8, 45.4],
                        [630, 15.4, 19.3, 24.1, 30.0, 37.4, 46.3, 57.2]
                    ]
                },
                "wall_thickness_tolerance": {
                    "description": "壁厚偏差表",
                    "source": "GB/T 4219.1 表1",
                    "columns": ["壁厚范围(mm)", "壁厚偏差(mm)"],
                    "data": [
                        ["1.0-2.0", 0.3],
                        ["2.1-3.0", 0.4],
                        ["3.1-4.0", 0.5],
                        ["4.1-6.0", 0.6],
                        ["6.1-10.0", 0.9],
                        ["10.1-16.0", 1.1],
                        ["16.1-25.0", 1.4],
                        ["25.1-40.0", 1.7],
                        ["40.1-60.0", 2.2]
                    ]
                }
            }
        elif domain == "fastener":
            return {
                "thread_spec_table": {
                    "description": "螺纹规格表",
                    "columns": ["规格", "螺距(mm)", "小径(mm)"],
                    "data": [
                        ["M6", 1.0, 4.917],
                        ["M8", 1.25, 6.647],
                        ["M10", 1.5, 8.376],
                        ["M12", 1.75, 10.106],
                        ["M16", 2.0, 13.835],
                        ["M20", 2.5, 17.294]
                    ]
                }
            }
        
        return {}
    
    def _infer_material_types(self, domain: str, standard: Standard) -> list:
        """推断适用物料类型"""
        domain_types = {
            "pipe": ["管材", "管道", "塑料管", "UPVC管", "PVC管", "PE管", "工业用管材"],
            "fastener": ["螺栓", "螺钉", "螺母", "紧固件"],
            "valve": ["阀门", "闸阀", "球阀", "蝶阀"],
            "fitting": ["管件", "弯头", "三通", "法兰"],
            "cable": ["电缆", "电线", "导线"],
            "bearing": ["轴承", "滚动轴承", "滑动轴承"],
            "seal": ["密封件", "垫片", "O型圈"],
        }
        
        return domain_types.get(domain, ["通用"])
    
    def _generate_output_structure(
        self, 
        attributes: Dict[str, Any], 
        category: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成输出模板结构"""
        # 动态生成规格参数
        spec_params = {}
        for attr_name, attr_def in attributes.items():
            display_name = attr_def.get("displayName", attr_name)
            spec_params[display_name] = f"{{{attr_name}}}"
        
        return {
            "materialName": "{材质}{类型} {规格}",
            "category": {
                "primary": category.get("primaryCategory", ""),
                "secondary": category.get("secondaryCategory", ""),
                "tertiary": category.get("tertiaryCategory", ""),
                "quaternary": category.get("quaternaryCategory", "")
            },
            "specParams": spec_params,
            "standardCode": "{standardCode}",
            "standardBasis": "{standardBasis}"
        }
