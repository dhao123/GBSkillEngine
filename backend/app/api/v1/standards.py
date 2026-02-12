"""
GBSkillEngine 国标管理API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import hashlib
import os
import uuid

from app.core.database import get_db
from app.models.standard import Standard, StandardStatus
from app.schemas.standard import (
    StandardCreate,
    StandardUpdate,
    StandardResponse,
    StandardListResponse,
    StandardUploadResponse,
    StandardCompileRequest,
    StandardCompileResponse
)
from app.config import settings

router = APIRouter(prefix="/standards", tags=["国标管理"])


@router.get("", response_model=StandardListResponse)
async def list_standards(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    domain: Optional[str] = None,
    status: Optional[StandardStatus] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取国标列表"""
    query = select(Standard)
    
    # 筛选条件
    if domain:
        query = query.where(Standard.domain == domain)
    if status:
        query = query.where(Standard.status == status)
    if keyword:
        query = query.where(
            Standard.standard_code.ilike(f"%{keyword}%") |
            Standard.standard_name.ilike(f"%{keyword}%")
        )
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分页
    query = query.order_by(Standard.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return StandardListResponse(total=total or 0, items=items)


@router.get("/{standard_id}", response_model=StandardResponse)
async def get_standard(
    standard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取国标详情"""
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    return standard


@router.post("", response_model=StandardResponse)
async def create_standard(
    data: StandardCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建国标"""
    # 检查是否已存在
    existing = await db.execute(
        select(Standard).where(Standard.standard_code == data.standard_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该国标编号已存在")
    
    standard = Standard(**data.model_dump())
    db.add(standard)
    await db.commit()
    await db.refresh(standard)
    
    return standard


@router.post("/upload", response_model=StandardUploadResponse)
async def upload_standard(
    file: UploadFile = File(...),
    standard_code: str = Form(...),
    standard_name: str = Form(...),
    version_year: Optional[str] = Form(None),
    domain: Optional[str] = Form(None),
    product_scope: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """上传国标文档"""
    # 检查文件类型
    allowed_types = [".pdf", ".doc", ".docx"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，仅支持: {', '.join(allowed_types)}")
    
    # 检查是否已存在
    existing = await db.execute(
        select(Standard).where(Standard.standard_code == standard_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该国标编号已存在")
    
    # 读取文件内容并计算hash
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 保存文件
    file_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.upload_dir, file_name)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建记录
    standard = Standard(
        standard_code=standard_code,
        standard_name=standard_name,
        version_year=version_year,
        domain=domain,
        product_scope=product_scope,
        file_path=file_path,
        file_type=file_ext[1:],
        file_hash=file_hash,
        status=StandardStatus.UPLOADED
    )
    
    db.add(standard)
    await db.commit()
    await db.refresh(standard)
    
    return StandardUploadResponse(
        id=standard.id,
        standard_code=standard.standard_code,
        status=standard.status.value,
        file_path=file_path,
        message="上传成功"
    )


@router.put("/{standard_id}", response_model=StandardResponse)
async def update_standard(
    standard_id: int,
    data: StandardUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新国标"""
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(standard, key, value)
    
    await db.commit()
    await db.refresh(standard)
    
    return standard


@router.delete("/{standard_id}")
async def delete_standard(
    standard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除国标"""
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    # 删除关联文件
    if standard.file_path and os.path.exists(standard.file_path):
        os.remove(standard.file_path)
    
    await db.delete(standard)
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/{standard_id}/compile", response_model=StandardCompileResponse)
async def compile_standard(
    standard_id: int,
    request: StandardCompileRequest,
    db: AsyncSession = Depends(get_db)
):
    """编译国标为Skill"""
    from app.services.skill_compiler.compiler import SkillCompiler
    
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    # 调用编译器
    compiler = SkillCompiler(db)
    skill = await compiler.compile(standard)
    
    # 更新国标状态
    standard.status = StandardStatus.COMPILED
    await db.commit()
    
    return StandardCompileResponse(
        skill_id=skill.skill_id,
        status="compiled",
        message="编译成功"
    )
