"""
GBSkillEngine 类目(Category)相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    """类目基础Schema"""
    category_code: str = Field(..., description="类目编码", example="pipe.seamless.carbon")
    category_name: str = Field(..., description="类目名称", example="碳素钢无缝钢管")
    level: int = Field(..., ge=1, le=4, description="层级(1-4)")
    description: Optional[str] = Field(None, description="类目描述")


class CategoryCreate(CategoryBase):
    """创建类目Schema"""
    parent_id: Optional[int] = Field(None, description="父类目ID")
    domain_id: Optional[int] = Field(None, description="所属领域ID")


class CategoryUpdate(BaseModel):
    """更新类目Schema"""
    category_name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    """类目响应Schema"""
    id: int
    parent_id: Optional[int] = None
    domain_id: Optional[int] = None
    full_path: Optional[str] = Field(None, description="完整路径")
    standard_count: int = Field(0, description="关联国标数量")
    skill_count: int = Field(0, description="关联Skill数量")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """类目列表响应"""
    total: int
    items: List[CategoryResponse]


class CategoryTreeNode(CategoryResponse):
    """类目树节点"""
    children: List["CategoryTreeNode"] = Field(default_factory=list)


class CategoryTree(BaseModel):
    """类目树响应"""
    domain_id: Optional[int] = None
    domain_name: Optional[str] = None
    roots: List[CategoryTreeNode] = Field(default_factory=list, description="顶级类目列表")


class CategoryHierarchy(BaseModel):
    """类目层级结构（用于创建层级）"""
    level1: str = Field(..., description="一级类目(领域)")
    level2: Optional[str] = Field(None, description="二级类目(产品大类)")
    level3: Optional[str] = Field(None, description="三级类目(具体产品)")
    level4: Optional[str] = Field(None, description="四级类目(规格)")
    domain_id: int = Field(..., description="领域ID")


# 处理循环引用
CategoryTreeNode.model_rebuild()
