"""
GBSkillEngine 物料梳理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.schemas.material import (
    MaterialParseRequest,
    MaterialParseResponse
)
from app.services.skill_runtime.runtime import SkillRuntime

router = APIRouter(prefix="/material-parse", tags=["物料梳理"])


@router.post("/single", response_model=MaterialParseResponse)
async def parse_single_material(
    request: MaterialParseRequest,
    db: AsyncSession = Depends(get_db)
):
    """单条物料梳理"""
    trace_id = str(uuid.uuid4())
    
    runtime = SkillRuntime(db)
    result = await runtime.execute(request.input_text, trace_id)
    
    return result


@router.post("/batch")
async def parse_batch_materials(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """批量物料梳理 (简化版本，同步处理)"""
    items = request.get("items", [])
    results = []
    
    runtime = SkillRuntime(db)
    
    for item in items:
        trace_id = str(uuid.uuid4())
        input_text = item.get("inputText", item.get("input_text", ""))
        
        if input_text:
            result = await runtime.execute(input_text, trace_id)
            results.append({
                "id": item.get("id"),
                "input_text": input_text,
                "result": result
            })
    
    return {
        "total": len(items),
        "completed": len(results),
        "results": results
    }
