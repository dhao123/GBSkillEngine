"""
GBSkillEngine 可观测API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.execution_log import ExecutionLog
from app.schemas.material import ExecutionLogResponse, ExecutionLogListResponse

router = APIRouter(prefix="/observability", tags=["可观测"])


@router.get("/execution-logs", response_model=ExecutionLogListResponse)
async def list_execution_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    skill_id: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取执行日志列表"""
    query = select(ExecutionLog)
    
    if skill_id:
        query = query.where(ExecutionLog.executed_skill_id == skill_id)
    if status:
        query = query.where(ExecutionLog.status == status)
    if start_time:
        query = query.where(ExecutionLog.created_at >= start_time)
    if end_time:
        query = query.where(ExecutionLog.created_at <= end_time)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(ExecutionLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ExecutionLogListResponse(total=total or 0, items=items)


@router.get("/execution-logs/{trace_id}")
async def get_execution_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取执行Trace详情"""
    result = await db.execute(
        select(ExecutionLog).where(ExecutionLog.trace_id == trace_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="执行日志不存在")
    
    return {
        "trace_id": log.trace_id,
        "input_text": log.input_text,
        "matched_skills": log.matched_skills,
        "executed_skill_id": log.executed_skill_id,
        "execution_trace": log.execution_trace,
        "output_result": log.output_result,
        "confidence_score": log.confidence_score,
        "execution_time_ms": log.execution_time_ms,
        "status": log.status,
        "error_message": log.error_message,
        "created_at": log.created_at
    }


@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db)
):
    """获取系统指标"""
    # 总执行次数
    total_result = await db.execute(select(func.count(ExecutionLog.id)))
    total_executions = total_result.scalar() or 0
    
    # 成功次数
    success_result = await db.execute(
        select(func.count(ExecutionLog.id)).where(ExecutionLog.status == "success")
    )
    success_count = success_result.scalar() or 0
    
    # 平均置信度
    avg_confidence_result = await db.execute(
        select(func.avg(ExecutionLog.confidence_score))
    )
    avg_confidence = avg_confidence_result.scalar() or 0
    
    # 平均执行时间
    avg_time_result = await db.execute(
        select(func.avg(ExecutionLog.execution_time_ms))
    )
    avg_execution_time = avg_time_result.scalar() or 0
    
    return {
        "total_executions": total_executions,
        "success_count": success_count,
        "success_rate": success_count / total_executions if total_executions > 0 else 0,
        "avg_confidence": round(float(avg_confidence), 3),
        "avg_execution_time_ms": round(float(avg_execution_time), 2)
    }
