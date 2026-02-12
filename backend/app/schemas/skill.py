"""
GBSkillEngine Skill相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.skill import SkillStatus


class SkillDSL(BaseModel):
    """Skill DSL Schema"""
    skillId: str = Field(..., description="Skill唯一标识")
    skillName: str = Field(..., description="Skill名称")
    version: str = Field("1.0.0", description="版本号")
    standardCode: Optional[str] = Field(None, description="关联国标编号")
    domain: Optional[str] = Field(None, description="领域")
    applicableMaterialTypes: Optional[List[str]] = Field(None, description="适用物料类型")
    priority: int = Field(100, description="优先级")
    
    intentRecognition: Optional[Dict[str, Any]] = Field(None, description="意图识别规则")
    attributeExtraction: Optional[Dict[str, Any]] = Field(None, description="属性抽取规则")
    rules: Optional[Dict[str, Any]] = Field(None, description="业务规则")
    tables: Optional[Dict[str, Any]] = Field(None, description="嵌入式数据表")
    enrichment: Optional[Dict[str, Any]] = Field(None, description="属性富化来源")
    categoryMapping: Optional[Dict[str, Any]] = Field(None, description="类目映射规则")
    outputStructure: Optional[Dict[str, Any]] = Field(None, description="输出模板")
    fallbackStrategy: Optional[Dict[str, Any]] = Field(None, description="回退策略")


class SkillBase(BaseModel):
    """Skill基础Schema"""
    skill_id: str = Field(..., description="Skill唯一标识")
    skill_name: str = Field(..., description="Skill名称")
    domain: Optional[str] = Field(None, description="领域")
    priority: int = Field(100, description="优先级")


class SkillCreate(BaseModel):
    """创建Skill Schema"""
    skill_id: str
    skill_name: str
    standard_id: Optional[int] = None
    domain: Optional[str] = None
    priority: int = 100
    applicable_material_types: Optional[List[str]] = None
    dsl_content: Dict[str, Any]


class SkillUpdate(BaseModel):
    """更新Skill Schema"""
    skill_name: Optional[str] = None
    domain: Optional[str] = None
    priority: Optional[int] = None
    applicable_material_types: Optional[List[str]] = None
    dsl_content: Optional[Dict[str, Any]] = None
    status: Optional[SkillStatus] = None


class SkillResponse(SkillBase):
    """Skill响应Schema"""
    id: int
    standard_id: Optional[int] = None
    applicable_material_types: Optional[List[str]] = None
    dsl_content: Dict[str, Any]
    dsl_version: str
    status: SkillStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """Skill列表响应"""
    total: int
    items: List[SkillResponse]


class SkillVersionResponse(BaseModel):
    """Skill版本响应"""
    id: int
    skill_id: int
    version: str
    dsl_content: Dict[str, Any]
    change_log: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
