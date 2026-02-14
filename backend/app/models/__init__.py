"""
GBSkillEngine 数据模型初始化
"""
from app.models.standard import Standard, StandardStatus
from app.models.skill import Skill, SkillVersion, SkillStatus
from app.models.execution_log import ExecutionLog
from app.models.llm_config import LLMConfig, LLMProvider, LLM_PROVIDER_INFO
from app.models.llm_usage_log import LLMUsageLog

# 新增数据模型
from app.models.standard_series import StandardSeries, detect_series
from app.models.domain import Domain, DOMAIN_PALETTE, allocate_domain_visual
from app.models.category import Category
from app.models.skill_family import SkillFamily, SkillFamilyMember
from app.models.attribute_definition import AttributeDefinition, DomainAttribute

__all__ = [
    # 原有模型
    "Standard",
    "StandardStatus",
    "Skill",
    "SkillVersion",
    "SkillStatus",
    "ExecutionLog",
    "LLMConfig",
    "LLMProvider",
    "LLM_PROVIDER_INFO",
    "LLMUsageLog",
    # 新增模型
    "StandardSeries",
    "detect_series",
    "Domain",
    "DOMAIN_PALETTE",
    "allocate_domain_visual",
    "Category",
    "SkillFamily",
    "SkillFamilyMember",
    "AttributeDefinition",
    "DomainAttribute",
]
