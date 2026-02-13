"""
GBSkillEngine 物料梳理相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MaterialParseRequest(BaseModel):
    """物料梳理请求"""
    input_text: str = Field(..., description="输入的物料描述", example="UPVC管PN1.6-DN100")


class MaterialParseBatchRequest(BaseModel):
    """批量物料梳理请求"""
    items: List[Dict[str, Any]] = Field(..., description="物料列表")


class EngineExecutionStep(BaseModel):
    """引擎执行步骤"""
    engine: str = Field(..., description="引擎名称")
    start_time: datetime
    end_time: datetime
    duration_ms: int
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    status: str = "success"
    message: Optional[str] = None


class ExecutionTrace(BaseModel):
    """执行Trace"""
    trace_id: str
    steps: List[EngineExecutionStep]
    total_duration_ms: int


class ParsedAttribute(BaseModel):
    """解析后的属性"""
    value: Any
    confidence: float = Field(..., ge=0, le=1)
    source: str = Field(..., description="来源: regex/llm/table/rule/default")
    unit: str = Field("", description="单位")
    displayName: str = Field("", description="显示名称")
    description: str = Field("", description="标准依据说明")


class MaterialParseResult(BaseModel):
    """物料梳理结果"""
    material_name: str = Field(..., description="物料名称")
    common_name: str = Field("", description="通用名称（标志要求的标准产品名称）")
    category: Dict[str, str] = Field(..., description="类目信息")
    attributes: Dict[str, ParsedAttribute] = Field(..., description="属性字典")
    standard_code: Optional[str] = Field(None, description="适用标准")
    confidence_score: float = Field(..., ge=0, le=1, description="整体置信度")


class MaterialParseResponse(BaseModel):
    """物料梳理响应"""
    trace_id: str
    result: MaterialParseResult
    execution_trace: ExecutionTrace
    matched_skill_id: Optional[str] = None


class BatchParseResponse(BaseModel):
    """批量梳理响应"""
    task_id: str
    status: str
    total: int
    completed: int


class ExecutionLogResponse(BaseModel):
    """执行日志响应"""
    id: int
    trace_id: str
    input_text: str
    executed_skill_id: Optional[str]
    output_result: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    execution_time_ms: Optional[int]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExecutionLogListResponse(BaseModel):
    """执行日志列表响应"""
    total: int
    items: List[ExecutionLogResponse]
