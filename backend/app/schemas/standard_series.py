"""
GBSkillEngine 标准系列(StandardSeries)相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StandardSeriesBase(BaseModel):
    """标准系列基础Schema"""
    series_code: str = Field(..., description="系列编号", example="GB/T 4219")
    series_name: Optional[str] = Field(None, description="系列名称")
    description: Optional[str] = Field(None, description="系列描述")


class StandardSeriesCreate(StandardSeriesBase):
    """创建标准系列Schema"""
    domain_id: Optional[int] = Field(None, description="所属领域ID")


class StandardSeriesUpdate(BaseModel):
    """更新标准系列Schema"""
    series_name: Optional[str] = None
    description: Optional[str] = None
    domain_id: Optional[int] = None


class StandardSeriesResponse(StandardSeriesBase):
    """标准系列响应Schema"""
    id: int
    domain_id: Optional[int] = None
    part_count: int = Field(1, description="分部数量")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StandardSeriesListResponse(BaseModel):
    """标准系列列表响应"""
    total: int
    items: List[StandardSeriesResponse]


class StandardSeriesWithStandards(StandardSeriesResponse):
    """带国标列表的系列响应"""
    standards: List[dict] = Field(default_factory=list, description="系列下的国标列表")
    domain_name: Optional[str] = Field(None, description="领域名称")


class SeriesDetectionResult(BaseModel):
    """系列检测结果"""
    series_code: str = Field(..., description="检测到的系列编号")
    part_number: Optional[int] = Field(None, description="分部编号")
    is_new_series: bool = Field(..., description="是否为新系列")
