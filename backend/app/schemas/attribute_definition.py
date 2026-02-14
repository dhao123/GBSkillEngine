"""
GBSkillEngine 属性定义(AttributeDefinition)相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class AttributeDefinitionBase(BaseModel):
    """属性定义基础Schema"""
    attribute_code: str = Field(..., description="属性编码", example="outer_diameter")
    attribute_name: str = Field(..., description="属性名称", example="外径")
    attribute_name_en: Optional[str] = Field(None, description="英文名称", example="Outer Diameter")
    data_type: str = Field("string", description="数据类型: string/number/enum/range/boolean")
    unit: Optional[str] = Field(None, description="单位", example="mm")
    description: Optional[str] = Field(None, description="属性描述")


class AttributeDefinitionCreate(AttributeDefinitionBase):
    """创建属性定义Schema"""
    patterns: Optional[List[str]] = Field(None, description="提取模式列表")
    synonyms: Optional[List[str]] = Field(None, description="同义词列表")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="校验规则")


class AttributeDefinitionUpdate(BaseModel):
    """更新属性定义Schema"""
    attribute_name: Optional[str] = None
    attribute_name_en: Optional[str] = None
    data_type: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    patterns: Optional[List[str]] = None
    synonyms: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class AttributeDefinitionResponse(AttributeDefinitionBase):
    """属性定义响应Schema"""
    id: int
    patterns: Optional[List[str]] = None
    synonyms: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    usage_count: int = Field(1, description="被引用次数")
    is_common: bool = Field(False, description="是否为通用属性")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AttributeDefinitionListResponse(BaseModel):
    """属性定义列表响应"""
    total: int
    items: List[AttributeDefinitionResponse]


class DomainAttributeBase(BaseModel):
    """领域-属性关联基础Schema"""
    domain_id: int = Field(..., description="领域ID")
    attribute_id: int = Field(..., description="属性定义ID")
    priority: int = Field(100, description="优先级")
    is_required: bool = Field(False, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")


class DomainAttributeCreate(DomainAttributeBase):
    """创建领域-属性关联Schema"""
    domain_specific_rules: Optional[Dict[str, Any]] = Field(None, description="领域特定规则")


class DomainAttributeResponse(DomainAttributeBase):
    """领域-属性关联响应Schema"""
    id: int
    domain_specific_rules: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DomainAttributeWithDetails(DomainAttributeResponse):
    """带属性详情的关联响应"""
    attribute: AttributeDefinitionResponse
    domain_name: Optional[str] = None


class AttributeByDomain(BaseModel):
    """按领域分组的属性列表"""
    domain_id: int
    domain_name: str
    domain_code: str
    attributes: List[DomainAttributeWithDetails]
