"""
GBSkillEngine 领域(Domain)相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DomainBase(BaseModel):
    """领域基础Schema"""
    domain_code: str = Field(..., description="领域编码", example="pipe")
    domain_name: str = Field(..., description="领域名称", example="管材管件")
    description: Optional[str] = Field(None, description="领域描述")


class DomainCreate(DomainBase):
    """创建领域Schema"""
    pass


class DomainUpdate(BaseModel):
    """更新领域Schema"""
    domain_name: Optional[str] = None
    description: Optional[str] = None


class DomainResponse(DomainBase):
    """领域响应Schema"""
    id: int
    color: str = Field(..., description="领域颜色(十六进制)")
    sector_angle: float = Field(..., description="3D图谱扇区角度")
    standard_count: int = Field(0, description="国标数量")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DomainListResponse(BaseModel):
    """领域列表响应"""
    total: int
    items: List[DomainResponse]


class DomainWithStats(DomainResponse):
    """带统计信息的领域响应"""
    series_count: int = Field(0, description="标准系列数量")
    skill_count: int = Field(0, description="Skill数量")
    category_count: int = Field(0, description="类目数量")
