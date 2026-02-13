"""
GBSkillEngine 国标管理API

提供国家标准文档的上传、查询、编辑、删除和编译功能。
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import hashlib
import os
import uuid
import mimetypes

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


@router.get(
    "", 
    response_model=StandardListResponse,
    summary="获取国标列表",
    description="分页查询国标列表，支持按领域、状态筛选和关键词搜索"
)
async def list_standards(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，最大100"),
    domain: Optional[str] = Query(None, description="筛选领域，如: 机械、电气"),
    status: Optional[StandardStatus] = Query(None, description="筛选状态: uploaded/compiled"),
    keyword: Optional[str] = Query(None, description="搜索关键词，匹配编号或名称"),
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


@router.get(
    "/{standard_id}", 
    response_model=StandardResponse,
    summary="获取国标详情",
    description="根据ID获取国标的完整信息"
)
async def get_standard(
    standard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取国标详情
    
    - **standard_id**: 国标记录ID
    """
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    return standard


@router.post(
    "", 
    response_model=StandardResponse,
    summary="创建国标记录",
    description="创建新的国标记录（不上传文件）"
)
async def create_standard(
    data: StandardCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建国标
    
    创建一条新的国标记录，需要提供国标编号和名称。
    国标编号必须唯一，重复的编号将返回400错误。
    """
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


@router.post(
    "/upload", 
    response_model=StandardUploadResponse,
    summary="上传国标文档",
    description="上传国标PDF/Word文档并创建记录"
)
async def upload_standard(
    file: UploadFile = File(..., description="国标文档文件(PDF/DOC/DOCX)"),
    standard_code: str = Form(..., description="国标编号，如 GB/T 1234-2024"),
    standard_name: str = Form(..., description="国标名称"),
    version_year: Optional[str] = Form(None, description="版本年份"),
    domain: Optional[str] = Form(None, description="适用领域"),
    product_scope: Optional[str] = Form(None, description="产品范围"),
    db: AsyncSession = Depends(get_db)
):
    """上传国标文档
    
    支持的文件格式: PDF, DOC, DOCX
    文件大小限制: 50MB
    """
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


@router.delete(
    "/{standard_id}",
    summary="删除国标",
    description="删除国标记录及其关联的文档文件"
)
async def delete_standard(
    standard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除国标
    
    同时删除数据库记录和上传的文档文件。
    此操作不可逆。
    """
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


@router.post(
    "/{standard_id}/compile", 
    response_model=StandardCompileResponse,
    summary="编译国标为Skill",
    description="将国标文档解析并编译为Skill DSL配置"
)
async def compile_standard(
    standard_id: int,
    request: StandardCompileRequest,
    db: AsyncSession = Depends(get_db)
):
    """编译国标为Skill
    
    解析国标文档内容，提取属性定义和规则，
    自动生成Skill DSL配置。
    
    编译过程包括:
    1. 文档解析和结构识别
    2. 属性提取和类型推断
    3. 规则生成和验证
    4. DSL配置生成
    """
    from app.services.skill_compiler import SkillCompilerFactory
    
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    # 使用工厂根据配置选择编译器
    compiler = SkillCompilerFactory.create(db, mode=request.mode if request else None)
    skill = await compiler.compile(standard)
    
    # 更新国标状态
    standard.status = StandardStatus.COMPILED
    await db.commit()
    
    return StandardCompileResponse(
        skill_id=skill.skill_id,
        status="compiled",
        message="编译成功"
    )


@router.get(
    "/{standard_id}/preview",
    summary="预览国标文档",
    description="在线预览国标PDF/Word文档",
    responses={
        200: {"description": "文档文件流"},
        404: {"description": "国标或文件不存在"}
    }
)
async def preview_standard_file(
    standard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """预览国标文档
    
    以inline方式返回文档，适合浏览器内嵌预览。
    """
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    if not standard.file_path or not os.path.exists(standard.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    # 获取MIME类型
    mime_type, _ = mimetypes.guess_type(standard.file_path)
    if not mime_type:
        if standard.file_type == 'pdf':
            mime_type = 'application/pdf'
        elif standard.file_type in ['doc', 'docx']:
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            mime_type = 'application/octet-stream'
    
    return FileResponse(
        path=standard.file_path,
        media_type=mime_type,
        filename=f"{standard.standard_code}.{standard.file_type}",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{standard.standard_code}.{standard.file_type}"
        }
    )


@router.get(
    "/{standard_id}/download",
    summary="下载国标文档",
    description="下载国标原始文档文件",
    responses={
        200: {"description": "文档文件下载"},
        404: {"description": "国标或文件不存在"}
    }
)
async def download_standard_file(
    standard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """下载国标文档
    
    以attachment方式返回文档，触发浏览器下载。
    """
    result = await db.execute(select(Standard).where(Standard.id == standard_id))
    standard = result.scalar_one_or_none()
    
    if not standard:
        raise HTTPException(status_code=404, detail="国标不存在")
    
    if not standard.file_path or not os.path.exists(standard.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    # 获取MIME类型
    mime_type, _ = mimetypes.guess_type(standard.file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    return FileResponse(
        path=standard.file_path,
        media_type=mime_type,
        filename=f"{standard.standard_code}.{standard.file_type}",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{standard.standard_code}.{standard.file_type}"
        }
    )
