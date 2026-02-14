"""
GBSkillEngine Skill管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.models.skill import Skill, SkillVersion, SkillStatus
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse,
    SkillVersionResponse
)

router = APIRouter(prefix="/skills", tags=["Skill管理"])


@router.get("", response_model=SkillListResponse)
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    domain: Optional[str] = None,
    status: Optional[SkillStatus] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取Skill列表"""
    query = select(Skill)
    
    if domain:
        query = query.where(Skill.domain == domain)
    if status:
        query = query.where(Skill.status == status)
    if keyword:
        query = query.where(
            Skill.skill_id.ilike(f"%{keyword}%") |
            Skill.skill_name.ilike(f"%{keyword}%")
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(Skill.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return SkillListResponse(total=total or 0, items=items)


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取Skill详情"""
    result = await db.execute(select(Skill).where(Skill.skill_id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill不存在")
    
    return skill


@router.post("", response_model=SkillResponse)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建Skill"""
    existing = await db.execute(
        select(Skill).where(Skill.skill_id == data.skill_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该Skill ID已存在")
    
    skill = Skill(**data.model_dump())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    
    # 创建初始版本
    version = SkillVersion(
        skill_id=skill.id,
        version="1.0.0",
        dsl_content=data.dsl_content,
        change_log="初始版本",
        is_active=True
    )
    db.add(version)
    await db.commit()
    
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新Skill"""
    result = await db.execute(select(Skill).where(Skill.skill_id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 如果更新了DSL内容，创建新版本
    if "dsl_content" in update_data:
        # 获取当前版本号
        current_version = skill.dsl_version
        parts = current_version.split(".")
        new_version = f"{parts[0]}.{int(parts[1]) + 1}.0"
        
        # 取消旧版本激活状态
        await db.execute(
            select(SkillVersion).where(
                SkillVersion.skill_id == skill.id,
                SkillVersion.is_active == True
            )
        )
        
        # 创建新版本
        version = SkillVersion(
            skill_id=skill.id,
            version=new_version,
            dsl_content=update_data["dsl_content"],
            change_log="更新DSL内容",
            is_active=True
        )
        db.add(version)
        skill.dsl_version = new_version
    
    for key, value in update_data.items():
        setattr(skill, key, value)
    
    await db.commit()
    await db.refresh(skill)
    
    return skill


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除Skill"""
    result = await db.execute(select(Skill).where(Skill.skill_id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill不存在")
    
    await db.delete(skill)
    await db.commit()
    
    return {"message": "删除成功"}


@router.put("/{skill_id}/activate")
async def activate_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """激活Skill"""
    result = await db.execute(select(Skill).where(Skill.skill_id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill不存在")
    
    skill.status = SkillStatus.ACTIVE
    await db.commit()
    
    return {"message": "激活成功", "status": skill.status}


@router.put("/{skill_id}/deactivate")
async def deactivate_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """停用Skill"""
    result = await db.execute(select(Skill).where(Skill.skill_id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill不存在")
    
    skill.status = SkillStatus.DEPRECATED
    await db.commit()
    
    return {"message": "停用成功", "status": skill.status}


@router.get("/{skill_id}/versions", response_model=list[SkillVersionResponse])
async def get_skill_versions(
    skill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取Skill版本历史"""
    result = await db.execute(select(Skill).where(Skill.skill_id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill不存在")
    
    versions_result = await db.execute(
        select(SkillVersion)
        .where(SkillVersion.skill_id == skill.id)
        .order_by(SkillVersion.created_at.desc())
    )
    versions = versions_result.scalars().all()
    
    return versions
