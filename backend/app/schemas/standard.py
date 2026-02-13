"""
GBSkillEngine 国标相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.standard import StandardStatus


class StandardBase(BaseModel):
    """国标基础Schema"""
    standard_code: str = Field(..., description="国标编号", example="GB/T 4219.1-2021")
    standard_name: str = Field(..., description="标准名称", example="工业用聚氯乙烯管道系统")
    version_year: Optional[str] = Field(None, description="版本年份", example="2021")
    domain: Optional[str] = Field(None, description="适用领域", example="pipe")
    product_scope: Optional[str] = Field(None, description="产品范围")


class StandardCreate(StandardBase):
    """创建国标Schema"""
    pass


class StandardUpdate(BaseModel):
    """更新国标Schema"""
    standard_name: Optional[str] = None
    version_year: Optional[str] = None
    domain: Optional[str] = None
    product_scope: Optional[str] = None
    status: Optional[StandardStatus] = None


class StandardResponse(StandardBase):
    """国标响应Schema"""
    id: int
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    status: StandardStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StandardListResponse(BaseModel):
    """国标列表响应"""
    total: int
    items: List[StandardResponse]


class StandardUploadResponse(BaseModel):
    """国标上传响应"""
    id: int
    standard_code: str
    status: str
    file_path: str
    message: str


class StandardCompileRequest(BaseModel):
    """Skill编译请求"""
    mode: Optional[str] = Field(None, description="编译模式: mock/real，默认使用系统配置")
    auto_generate: bool = Field(True, description="是否自动生成")
    review_before_publish: bool = Field(True, description="发布前是否需要审核")


class StandardCompileResponse(BaseModel):
    """Skill编译响应"""
    skill_id: str
    status: str
    task_id: Optional[str] = None
    message: str
