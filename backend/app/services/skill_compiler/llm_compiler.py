"""
GBSkillEngine LLM Skill编译器

使用LLM将国标文档编译为Skill DSL
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
import re

from app.models.standard import Standard
from app.models.skill import Skill, SkillStatus
from app.services.llm.base import BaseLLMProvider, LLMError
from app.services.llm.factory import get_default_provider
from app.services.skill_compiler.prompts import (
    SYSTEM_PROMPT,
    DOMAIN_DETECTION_PROMPT,
    ATTRIBUTE_EXTRACTION_PROMPT,
    INTENT_RECOGNITION_PROMPT,
    CATEGORY_MAPPING_PROMPT,
    FULL_DSL_GENERATION_PROMPT,
)
from app.config import settings

logger = logging.getLogger(__name__)


class LLMSkillCompiler:
    """LLM驱动的Skill编译器"""
    
    def __init__(self, db: AsyncSession, llm_provider: Optional[BaseLLMProvider] = None):
        self.db = db
        self._llm_provider = llm_provider
    
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
        
        # Step 5: 组装完整DSL
        dsl = self._assemble_dsl(standard, domain, attributes, intent, category)
        
        # Step 6: 验证DSL
        self._validate_dsl(dsl)
        
        # Step 7: 创建Skill记录
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
            document_summary=self._get_document_summary(standard)
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
    
    def _assemble_dsl(
        self,
        standard: Standard,
        domain: str,
        attributes: Dict[str, Any],
        intent: Dict[str, Any],
        category: Dict[str, Any]
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
            "tables": {},
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
    
    def _get_document_summary(self, standard: Standard) -> str:
        """获取文档摘要"""
        parts = []
        
        if standard.product_scope:
            parts.append(f"产品范围: {standard.product_scope}")
        
        if standard.technical_requirements:
            parts.append(f"技术要求: {standard.technical_requirements[:500]}")
        
        return "\n".join(parts) if parts else "无文档摘要"
    
    def _get_default_attributes(self, domain: str) -> Dict[str, Any]:
        """获取默认属性定义"""
        defaults = {
            "pipe": {
                "公称直径": {
                    "type": "dimension",
                    "unit": "mm",
                    "patterns": ["DN(\\d+)", "dn(\\d+)", "直径(\\d+)"],
                    "required": True
                },
                "公称压力": {
                    "type": "dimension",
                    "unit": "MPa",
                    "patterns": ["PN([\\d.]+)", "pn([\\d.]+)"],
                    "required": False
                },
                "材质": {
                    "type": "material",
                    "patterns": ["(UPVC|PVC-U|PVC|PE|PPR|PP-R)"],
                    "required": False,
                    "defaultValue": "PVC-U"
                }
            },
            "fastener": {
                "规格": {
                    "type": "specification",
                    "patterns": ["M(\\d+)[×x](\\d+)", "M(\\d+)"],
                    "required": True
                },
                "材质": {
                    "type": "material",
                    "patterns": ["(碳钢|不锈钢|304|316|Q235)"],
                    "required": False,
                    "defaultValue": "碳钢"
                },
                "性能等级": {
                    "type": "performance",
                    "patterns": ["([\\d.]+)级", "等级([\\d.]+)"],
                    "allowedValues": ["4.8", "8.8", "10.9", "12.9"],
                    "required": False
                }
            }
        }
        
        return defaults.get(domain, {
            "规格型号": {
                "type": "specification",
                "patterns": ["([A-Za-z0-9-]+)"],
                "required": True
            }
        })
    
    def _get_default_intent(self, domain: str) -> Dict[str, Any]:
        """获取默认意图识别规则"""
        defaults = {
            "pipe": {
                "keywords": ["管", "管材", "管道", "DN", "PN", "UPVC", "PVC", "PE", "PPR"],
                "patterns": ["(DN|dn)\\d+", "(PN|pn)[\\d.]+", "UPVC|PVC|PE|PPR"]
            },
            "fastener": {
                "keywords": ["螺栓", "螺钉", "螺母", "垫片", "M6", "M8", "M10", "M12"],
                "patterns": ["M\\d+[×x]?\\d*", "螺栓|螺钉|螺母"]
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
                "primaryCategory": "管材",
                "secondaryCategory": "塑料管",
                "tertiaryCategory": "PVC-U管",
                "categoryId": "CAT_PIPE_001"
            },
            "fastener": {
                "primaryCategory": "紧固件",
                "secondaryCategory": "螺栓",
                "tertiaryCategory": "六角头螺栓",
                "categoryId": "CAT_FASTENER_001"
            }
        }
        
        return defaults.get(domain, {
            "primaryCategory": "通用",
            "secondaryCategory": "其他",
            "tertiaryCategory": "未分类",
            "categoryId": "CAT_GENERAL_001"
        })
    
    def _infer_material_types(self, domain: str, standard: Standard) -> list:
        """推断适用物料类型"""
        domain_types = {
            "pipe": ["管材", "管道", "塑料管", "UPVC管", "PVC管", "PE管"],
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
        for attr_name in attributes.keys():
            spec_params[attr_name] = f"{{{attr_name}}}"
        
        return {
            "物料名称": "{材质}{类型} {规格}",
            "类目": f"{category.get('primaryCategory', '')}/{category.get('secondaryCategory', '')}/{category.get('tertiaryCategory', '')}",
            "规格参数": spec_params,
            "适用标准": "{standardCode}"
        }
