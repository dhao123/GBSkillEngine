"""
GBSkillEngine LLM配置数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Float, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class LLMProvider(str, enum.Enum):
    """LLM供应商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ZKH = "zkh"             # 震坤行大模型服务
    LOCAL = "local"         # 本地模型 (Ollama等)


class LLMConfig(Base):
    """LLM配置表"""
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基本信息
    provider = Column(SQLEnum(LLMProvider), nullable=False, comment="LLM供应商")
    name = Column(String(100), nullable=False, comment="配置名称")
    
    # API认证 (加密存储)
    api_key_encrypted = Column(Text, nullable=True, comment="加密后的API Key")
    api_key_iv = Column(String(32), nullable=True, comment="加密初始化向量")
    api_secret_encrypted = Column(Text, nullable=True, comment="加密后的API Secret (部分供应商需要)")
    api_secret_iv = Column(String(32), nullable=True, comment="Secret加密初始化向量")
    
    # 模型配置
    model_name = Column(String(100), nullable=False, comment="模型名称")
    endpoint = Column(String(500), nullable=True, comment="自定义API端点")
    
    # 生成参数
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=4096, comment="最大Token数")
    timeout = Column(Integer, default=60, comment="请求超时(秒)")
    
    # 状态标记
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<LLMConfig {self.id}: {self.name} ({self.provider.value})>"


# 供应商信息配置
LLM_PROVIDER_INFO = {
    LLMProvider.OPENAI: {
        "name": "OpenAI",
        "description": "OpenAI GPT系列模型",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "default_endpoint": "https://api.openai.com/v1",
        "requires_secret": False,
        "supports_custom_endpoint": True,
    },
    LLMProvider.ANTHROPIC: {
        "name": "Anthropic",
        "description": "Anthropic Claude系列模型",
        "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"],
        "default_endpoint": "https://api.anthropic.com",
        "requires_secret": False,
        "supports_custom_endpoint": True,
    },
    LLMProvider.ZKH: {
        "name": "震坤行",
        "description": "震坤行大模型服务 (兼容OpenAI API)",
        "models": ["ep_20250805_urdq", "ep_20251217_i18v", "ep_20250805_ur59", "ep_20250728_izkl"],
        "default_endpoint": "https://ai-dev-gateway.zkh360.com/llm/v1",
        "requires_secret": False,
        "supports_custom_endpoint": True,
    },
    LLMProvider.LOCAL: {
        "name": "本地模型",
        "description": "本地部署的模型 (Ollama, vLLM等)",
        "models": ["llama3", "mistral", "qwen2", "deepseek-coder"],
        "default_endpoint": "http://localhost:11434",
        "requires_secret": False,
        "supports_custom_endpoint": True,
    },
}
