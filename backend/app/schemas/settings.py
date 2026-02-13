"""
GBSkillEngine Settings相关Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.llm_config import LLMProvider


# ==================== LLM配置 Schema ====================

class LLMConfigBase(BaseModel):
    """LLM配置基础Schema"""
    provider: LLMProvider = Field(..., description="LLM供应商")
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    endpoint: Optional[str] = Field(None, max_length=500, description="自定义API端点")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(4096, ge=1, le=128000, description="最大Token数")
    timeout: int = Field(60, ge=1, le=600, description="请求超时(秒)")


class LLMConfigCreate(LLMConfigBase):
    """创建LLM配置Schema"""
    api_key: str = Field(..., min_length=1, description="API Key (明文)")
    api_secret: Optional[str] = Field(None, description="API Secret (部分供应商需要)")
    is_default: bool = Field(False, description="是否设为默认配置")
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise ValueError('API Key不能为空')
        return v.strip()


class LLMConfigUpdate(BaseModel):
    """更新LLM配置Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    endpoint: Optional[str] = Field(None, max_length=500)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    timeout: Optional[int] = Field(None, ge=1, le=600)
    api_key: Optional[str] = Field(None, description="新的API Key (不传则不更新)")
    api_secret: Optional[str] = Field(None, description="新的API Secret")
    is_active: Optional[bool] = Field(None)


class LLMConfigResponse(LLMConfigBase):
    """LLM配置响应Schema"""
    id: int
    api_key_masked: str = Field(..., description="脱敏后的API Key")
    has_api_secret: bool = Field(False, description="是否配置了API Secret")
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LLMConfigListResponse(BaseModel):
    """LLM配置列表响应"""
    total: int
    items: List[LLMConfigResponse]


# ==================== 连接测试 Schema ====================

class ConnectionTestRequest(BaseModel):
    """连接测试请求"""
    test_prompt: Optional[str] = Field(
        "Hello, please respond with 'OK' if you can read this.",
        description="测试用的提示词"
    )


class ConnectionTestResponse(BaseModel):
    """连接测试响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    latency_ms: Optional[int] = Field(None, description="响应延迟(毫秒)")
    model_info: Optional[Dict[str, Any]] = Field(None, description="模型信息")


# ==================== 供应商信息 Schema ====================

class LLMProviderInfo(BaseModel):
    """LLM供应商信息"""
    provider: LLMProvider
    name: str
    description: str
    models: List[str]
    default_endpoint: str
    requires_secret: bool
    supports_custom_endpoint: bool


class LLMProviderListResponse(BaseModel):
    """供应商列表响应"""
    providers: List[LLMProviderInfo]


# ==================== 系统信息 Schema ====================

class SystemInfo(BaseModel):
    """系统信息"""
    version: str = Field("1.0.0", description="系统版本")
    llm_mode: str = Field(..., description="当前LLM模式 (mock/real)")
    default_llm_config_id: Optional[int] = Field(None, description="默认LLM配置ID")
    default_llm_provider: Optional[str] = Field(None, description="默认LLM供应商")
    default_llm_model: Optional[str] = Field(None, description="默认LLM模型")


# ==================== 通用响应 Schema ====================

class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error_code: str
    message: str
    detail: Optional[str] = None


# ==================== LLM使用监控 Schema ====================

class LLMUsageLogResponse(BaseModel):
    """LLM调用记录响应"""
    id: int
    config_id: Optional[int]
    provider: str
    model_name: str
    caller: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    success: bool
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LLMUsageLogListResponse(BaseModel):
    """调用记录列表响应"""
    total: int
    items: List[LLMUsageLogResponse]


class UsageTrendPoint(BaseModel):
    """使用趋势数据点"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    total_tokens: int = Field(0, description="总Token数")
    prompt_tokens: int = Field(0, description="输入Token数")
    completion_tokens: int = Field(0, description="输出Token数")
    total_calls: int = Field(0, description="总调用次数")
    success_calls: int = Field(0, description="成功调用次数")
    failed_calls: int = Field(0, description="失败调用次数")
    avg_latency_ms: float = Field(0, description="平均延迟(ms)")


class UsageSummary(BaseModel):
    """使用量汇总"""
    total_calls: int = Field(0, description="总调用次数")
    total_tokens: int = Field(0, description="总Token数")
    total_prompt_tokens: int = Field(0, description="总输入Token")
    total_completion_tokens: int = Field(0, description="总输出Token")
    avg_latency_ms: float = Field(0, description="平均延迟")
    success_rate: float = Field(0, description="成功率 0-1")
    by_provider: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="按供应商汇总")
    by_model: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="按模型汇总")


class UsageMonitorResponse(BaseModel):
    """监控数据响应"""
    summary: UsageSummary
    trend: List[UsageTrendPoint]
