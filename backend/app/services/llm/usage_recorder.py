"""
GBSkillEngine LLM调用记录器

在每次LLM调用后自动记录使用数据，供监控和分析使用
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.llm_usage_log import LLMUsageLog
from app.services.llm.base import LLMResponse

logger = logging.getLogger(__name__)


async def record_llm_usage(
    db: AsyncSession,
    provider: str,
    model_name: str,
    response: Optional[LLMResponse] = None,
    config_id: Optional[int] = None,
    caller: Optional[str] = None,
    prompt_preview: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    latency_ms: int = 0,
) -> LLMUsageLog:
    """
    记录一次LLM调用

    Args:
        db: 数据库会话
        provider: 供应商标识
        model_name: 模型名称
        response: LLM响应对象 (成功时)
        config_id: 关联的配置ID
        caller: 调用方标识
        prompt_preview: 提示词摘要
        success: 是否成功
        error_message: 错误信息 (失败时)
        latency_ms: 延迟毫秒

    Returns:
        LLMUsageLog记录
    """
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    if response:
        prompt_tokens = response.prompt_tokens
        completion_tokens = response.completion_tokens
        total_tokens = response.total_tokens
        latency_ms = latency_ms or response.latency_ms

    # 截断prompt_preview
    if prompt_preview and len(prompt_preview) > 500:
        prompt_preview = prompt_preview[:497] + "..."

    log_entry = LLMUsageLog(
        config_id=config_id,
        provider=provider,
        model_name=model_name,
        caller=caller,
        prompt_preview=prompt_preview,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        success=success,
        error_message=error_message,
    )

    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    return log_entry
