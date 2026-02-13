"""
GBSkillEngine LLM调用记录数据模型

记录每次LLM调用的tokens消耗、延迟等指标，用于监控和成本分析
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class LLMUsageLog(Base):
    """LLM调用记录表"""
    __tablename__ = "llm_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联配置
    config_id = Column(Integer, nullable=True, index=True, comment="关联的LLM配置ID")
    provider = Column(String(50), nullable=False, index=True, comment="供应商")
    model_name = Column(String(100), nullable=False, index=True, comment="模型名称")
    
    # 调用信息
    caller = Column(String(100), nullable=True, comment="调用方 (compile/test/parse等)")
    prompt_preview = Column(String(500), nullable=True, comment="提示词摘要 (截断)")
    
    # Token指标
    prompt_tokens = Column(Integer, default=0, comment="输入Token数")
    completion_tokens = Column(Integer, default=0, comment="输出Token数")
    total_tokens = Column(Integer, default=0, comment="总Token数")
    
    # 性能指标
    latency_ms = Column(Integer, default=0, comment="响应延迟(毫秒)")
    
    # 结果
    success = Column(Boolean, default=True, comment="是否成功")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="调用时间")
    
    def __repr__(self):
        return f"<LLMUsageLog {self.id}: {self.provider}/{self.model_name} {self.total_tokens}tokens>"
