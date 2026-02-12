"""
GBSkillEngine 执行日志数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from app.core.database import Base


class ExecutionLog(Base):
    """Skill执行日志表"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trace_id = Column(String(64), unique=True, nullable=False, index=True, comment="追踪ID")
    input_text = Column(Text, nullable=False, comment="输入的物料描述")
    matched_skills = Column(JSON, nullable=True, comment="匹配到的Skill列表")
    executed_skill_id = Column(String(200), nullable=True, index=True, comment="实际执行的Skill ID")
    execution_trace = Column(JSON, nullable=True, comment="执行Trace")
    output_result = Column(JSON, nullable=True, comment="结构化输出结果")
    confidence_score = Column(Float, nullable=True, comment="整体置信度")
    execution_time_ms = Column(Integer, nullable=True, comment="执行耗时(ms)")
    status = Column(String(50), default="success", comment="状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="执行时间")
    
    def __repr__(self):
        return f"<ExecutionLog {self.trace_id}>"
