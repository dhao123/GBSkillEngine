"""
GBSkillEngine 技能族(SkillFamily)相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SkillFamilyBase(BaseModel):
    """技能族基础Schema"""
    family_code: str = Field(..., description="技能族编码", example="family_GBT_4219")
    family_name: str = Field(..., description="技能族名称")
    description: Optional[str] = Field(None, description="技能族描述")


class SkillFamilyCreate(SkillFamilyBase):
    """创建技能族Schema"""
    series_id: Optional[int] = Field(None, description="关联的标准系列ID")
    domain_id: Optional[int] = Field(None, description="所属领域ID")


class SkillFamilyUpdate(BaseModel):
    """更新技能族Schema"""
    family_name: Optional[str] = None
    description: Optional[str] = None


class SkillFamilyResponse(SkillFamilyBase):
    """技能族响应Schema"""
    id: int
    series_id: Optional[int] = None
    domain_id: Optional[int] = None
    skill_count: int = Field(0, description="族内Skill数量")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SkillFamilyListResponse(BaseModel):
    """技能族列表响应"""
    total: int
    items: List[SkillFamilyResponse]


class SkillFamilyMemberBase(BaseModel):
    """技能族成员基础Schema"""
    family_id: int = Field(..., description="技能族ID")
    skill_id: int = Field(..., description="Skill ID")
    role: str = Field("member", description="角色: primary/member")


class SkillFamilyMemberCreate(SkillFamilyMemberBase):
    """创建技能族成员Schema"""
    pass


class SkillFamilyMemberResponse(SkillFamilyMemberBase):
    """技能族成员响应Schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SkillFamilyWithMembers(SkillFamilyResponse):
    """带成员列表的技能族响应"""
    members: List[dict] = Field(default_factory=list, description="族内Skill摘要列表")
    series_code: Optional[str] = Field(None, description="关联系列编号")
    domain_name: Optional[str] = Field(None, description="领域名称")
