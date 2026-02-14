"""
GBSkillEngine Benchmark 评测系统 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.benchmark import (
    BenchmarkDataset, BenchmarkCase, BenchmarkRun, BenchmarkResult, GenerationTemplate,
    DatasetSourceType, DatasetStatus, CaseDifficulty, CaseSourceType, RunStatus, ResultStatus
)
from app.schemas.benchmark import (
    # Dataset
    BenchmarkDatasetCreate, BenchmarkDatasetUpdate, BenchmarkDatasetResponse,
    BenchmarkDatasetListResponse,
    # Case
    BenchmarkCaseCreate, BenchmarkCaseUpdate, BenchmarkCaseResponse,
    BenchmarkCaseListResponse, BenchmarkCaseBatchCreate,
    # Generation
    GenerationOptions, GenerationResult,
    # Run
    BenchmarkRunCreate, BenchmarkRunResponse, BenchmarkRunListResponse,
    EvaluationConfig,
    # Result
    BenchmarkResultResponse, BenchmarkResultListResponse, BenchmarkMetrics,
    # Template
    GenerationTemplateCreate, GenerationTemplateUpdate, GenerationTemplateResponse,
    GenerationTemplateListResponse, TemplatePreviewRequest, TemplatePreviewResponse
)
from app.services.benchmark import BenchmarkDataGenerator, BenchmarkEvaluationService

router = APIRouter(prefix="/benchmark", tags=["评测系统"])


# ============= 数据集管理 =============

@router.get("/datasets", response_model=BenchmarkDatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[DatasetStatus] = None,
    source_type: Optional[DatasetSourceType] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取数据集列表"""
    query = select(BenchmarkDataset)
    
    if status:
        query = query.where(BenchmarkDataset.status == status)
    if source_type:
        query = query.where(BenchmarkDataset.source_type == source_type)
    if keyword:
        query = query.where(
            BenchmarkDataset.dataset_code.ilike(f"%{keyword}%") |
            BenchmarkDataset.dataset_name.ilike(f"%{keyword}%")
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(BenchmarkDataset.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return BenchmarkDatasetListResponse(total=total or 0, items=items)


@router.get("/datasets/{dataset_id}", response_model=BenchmarkDatasetResponse)
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取数据集详情"""
    result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    return dataset


@router.post("/datasets", response_model=BenchmarkDatasetResponse)
async def create_dataset(
    data: BenchmarkDatasetCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建数据集"""
    # 检查编码唯一性
    existing = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.dataset_code == data.dataset_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该数据集编码已存在")
    
    dataset = BenchmarkDataset(**data.model_dump())
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    return dataset


@router.put("/datasets/{dataset_id}", response_model=BenchmarkDatasetResponse)
async def update_dataset(
    dataset_id: int,
    data: BenchmarkDatasetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新数据集"""
    result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dataset, key, value)
    
    await db.commit()
    await db.refresh(dataset)
    
    return dataset


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除数据集"""
    result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    # 检查是否有正在运行的评测
    run_result = await db.execute(
        select(BenchmarkRun).where(
            BenchmarkRun.dataset_id == dataset_id,
            BenchmarkRun.status == RunStatus.RUNNING
        )
    )
    if run_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="存在进行中的评测运行，无法删除")
    
    await db.delete(dataset)
    await db.commit()
    
    return {"message": "删除成功"}


# ============= 测试用例管理 =============

@router.get("/datasets/{dataset_id}/cases", response_model=BenchmarkCaseListResponse)
async def list_cases(
    dataset_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: Optional[CaseDifficulty] = None,
    source_type: Optional[CaseSourceType] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取数据集的测试用例列表"""
    query = select(BenchmarkCase).where(BenchmarkCase.dataset_id == dataset_id)
    
    if difficulty:
        query = query.where(BenchmarkCase.difficulty == difficulty)
    if source_type:
        query = query.where(BenchmarkCase.source_type == source_type)
    if is_active is not None:
        query = query.where(BenchmarkCase.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(BenchmarkCase.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return BenchmarkCaseListResponse(total=total or 0, items=items)


@router.get("/cases/{case_id}", response_model=BenchmarkCaseResponse)
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例详情"""
    result = await db.execute(
        select(BenchmarkCase).where(BenchmarkCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    return case


@router.post("/datasets/{dataset_id}/cases", response_model=BenchmarkCaseResponse)
async def create_case(
    dataset_id: int,
    data: BenchmarkCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试用例"""
    # 检查数据集是否存在
    result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    # 生成用例编码
    case_code = data.case_code or f"CASE_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
    
    # 转换 expected_attributes
    expected_attrs = {}
    for k, v in data.expected_attributes.items():
        if hasattr(v, 'model_dump'):
            expected_attrs[k] = v.model_dump()
        else:
            expected_attrs[k] = v
    
    case = BenchmarkCase(
        dataset_id=dataset_id,
        case_code=case_code,
        input_text=data.input_text,
        expected_skill_id=data.expected_skill_id,
        expected_attributes=expected_attrs,
        expected_category=data.expected_category,
        difficulty=data.difficulty,
        source_type=data.source_type,
        source_reference=data.source_reference,
        tags=data.tags,
        is_active=True
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    # 更新数据集统计
    await _update_dataset_case_count(db, dataset_id)
    
    return case


@router.post("/datasets/{dataset_id}/cases/batch")
async def batch_create_cases(
    dataset_id: int,
    data: BenchmarkCaseBatchCreate,
    db: AsyncSession = Depends(get_db)
):
    """批量创建测试用例"""
    # 检查数据集是否存在
    result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    created_count = 0
    for case_data in data.cases:
        case_code = case_data.case_code or f"CASE_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
        expected_attrs = {}
        for k, v in case_data.expected_attributes.items():
            if hasattr(v, 'model_dump'):
                expected_attrs[k] = v.model_dump()
            else:
                expected_attrs[k] = v
        
        case = BenchmarkCase(
            dataset_id=dataset_id,
            case_code=case_code,
            input_text=case_data.input_text,
            expected_skill_id=case_data.expected_skill_id,
            expected_attributes=expected_attrs,
            expected_category=case_data.expected_category,
            difficulty=case_data.difficulty,
            source_type=case_data.source_type,
            source_reference=case_data.source_reference,
            tags=case_data.tags,
            is_active=True
        )
        db.add(case)
        created_count += 1
    
    await db.commit()
    await _update_dataset_case_count(db, dataset_id)
    
    return {"message": f"成功创建 {created_count} 个测试用例"}


@router.put("/cases/{case_id}", response_model=BenchmarkCaseResponse)
async def update_case(
    case_id: int,
    data: BenchmarkCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例"""
    result = await db.execute(
        select(BenchmarkCase).where(BenchmarkCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 处理 expected_attributes
    if "expected_attributes" in update_data and update_data["expected_attributes"]:
        attrs = {}
        for k, v in update_data["expected_attributes"].items():
            if hasattr(v, 'model_dump'):
                attrs[k] = v.model_dump()
            else:
                attrs[k] = v
        update_data["expected_attributes"] = attrs
    
    for key, value in update_data.items():
        setattr(case, key, value)
    
    await db.commit()
    await db.refresh(case)
    
    return case


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除测试用例"""
    result = await db.execute(
        select(BenchmarkCase).where(BenchmarkCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    dataset_id = case.dataset_id
    await db.delete(case)
    await db.commit()
    
    await _update_dataset_case_count(db, dataset_id)
    
    return {"message": "删除成功"}


# ============= 数据生成 =============

@router.post("/datasets/{dataset_id}/generate", response_model=GenerationResult)
async def generate_cases(
    dataset_id: int,
    options: GenerationOptions,
    db: AsyncSession = Depends(get_db)
):
    """从 Skill 自动生成测试用例"""
    # 检查数据集是否存在
    result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    generator = BenchmarkDataGenerator(db)
    
    try:
        gen_result = await generator.generate_from_skill(
            skill_id=options.skill_id,
            options=options,
            dataset_id=dataset_id
        )
        await db.commit()
        return gen_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# ============= 评测运行 =============

@router.get("/runs", response_model=BenchmarkRunListResponse)
async def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    dataset_id: Optional[int] = None,
    status: Optional[RunStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取评测运行列表"""
    query = select(BenchmarkRun)
    
    if dataset_id:
        query = query.where(BenchmarkRun.dataset_id == dataset_id)
    if status:
        query = query.where(BenchmarkRun.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(BenchmarkRun.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    runs = result.scalars().all()
    
    # 添加 progress 字段
    items = []
    for run in runs:
        run_dict = {
            "id": run.id,
            "run_code": run.run_code,
            "dataset_id": run.dataset_id,
            "run_name": run.run_name,
            "description": run.description,
            "config": run.config,
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "total_cases": run.total_cases,
            "completed_cases": run.completed_cases,
            "progress": (run.completed_cases / run.total_cases * 100) if run.total_cases > 0 else 0,
            "metrics": run.metrics,
            "created_at": run.created_at,
            "created_by": run.created_by
        }
        items.append(BenchmarkRunResponse(**run_dict))
    
    return BenchmarkRunListResponse(total=total or 0, items=items)


@router.get("/runs/{run_id}", response_model=BenchmarkRunResponse)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取评测运行详情"""
    result = await db.execute(
        select(BenchmarkRun).where(BenchmarkRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="评测运行不存在")
    
    return BenchmarkRunResponse(
        id=run.id,
        run_code=run.run_code,
        dataset_id=run.dataset_id,
        run_name=run.run_name,
        description=run.description,
        config=run.config,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_cases=run.total_cases,
        completed_cases=run.completed_cases,
        progress=(run.completed_cases / run.total_cases * 100) if run.total_cases > 0 else 0,
        metrics=run.metrics,
        created_at=run.created_at,
        created_by=run.created_by
    )


@router.post("/runs", response_model=BenchmarkRunResponse)
async def create_run(
    data: BenchmarkRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """创建评测运行"""
    eval_service = BenchmarkEvaluationService(db)
    
    try:
        run = await eval_service.create_run(
            dataset_id=data.dataset_id,
            run_name=data.run_name,
            description=data.description,
            config=data.config
        )
        await db.commit()
        
        return BenchmarkRunResponse(
            id=run.id,
            run_code=run.run_code,
            dataset_id=run.dataset_id,
            run_name=run.run_name,
            description=run.description,
            config=run.config,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            total_cases=run.total_cases,
            completed_cases=run.completed_cases,
            progress=0,
            metrics=run.metrics,
            created_at=run.created_at,
            created_by=run.created_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/execute")
async def execute_run(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """执行评测运行"""
    eval_service = BenchmarkEvaluationService(db)
    
    try:
        run = await eval_service.execute_run(run_id)
        return {
            "message": "评测执行完成",
            "run_id": run.id,
            "status": run.status,
            "completed_cases": run.completed_cases,
            "total_cases": run.total_cases
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评测执行失败: {str(e)}")


@router.get("/runs/{run_id}/metrics", response_model=BenchmarkMetrics)
async def get_run_metrics(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取评测运行的指标汇总"""
    result = await db.execute(
        select(BenchmarkRun).where(BenchmarkRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="评测运行不存在")
    
    if not run.metrics:
        raise HTTPException(status_code=400, detail="评测尚未完成")
    
    return BenchmarkMetrics(**run.metrics)


@router.get("/runs/{run_id}/results", response_model=BenchmarkResultListResponse)
async def get_run_results(
    run_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ResultStatus] = None,
    difficulty: Optional[CaseDifficulty] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取评测运行的结果列表"""
    query = select(BenchmarkResult, BenchmarkCase).join(
        BenchmarkCase, BenchmarkResult.case_id == BenchmarkCase.id
    ).where(BenchmarkResult.run_id == run_id)
    
    if status:
        query = query.where(BenchmarkResult.status == status)
    if difficulty:
        query = query.where(BenchmarkCase.difficulty == difficulty)
    
    # 统计总数
    count_query = select(func.count()).select_from(
        select(BenchmarkResult).where(BenchmarkResult.run_id == run_id).subquery()
    )
    total = await db.scalar(count_query)
    
    query = query.order_by(BenchmarkResult.id)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for bench_result, case in rows:
        items.append(BenchmarkResultResponse(
            id=bench_result.id,
            run_id=bench_result.run_id,
            case_id=bench_result.case_id,
            actual_skill_id=bench_result.actual_skill_id,
            actual_attributes=bench_result.actual_attributes,
            actual_category=bench_result.actual_category,
            actual_confidence=bench_result.actual_confidence,
            execution_time_ms=bench_result.execution_time_ms,
            skill_match=bench_result.skill_match,
            attribute_scores=bench_result.attribute_scores,
            overall_score=bench_result.overall_score,
            status=bench_result.status,
            error_message=bench_result.error_message,
            created_at=bench_result.created_at,
            case_code=case.case_code,
            input_text=case.input_text,
            difficulty=case.difficulty.value if case.difficulty else None
        ))
    
    return BenchmarkResultListResponse(total=total or 0, items=items)


@router.get("/runs/{run_id}/failed-cases")
async def get_failed_cases(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取失败用例详情，用于分析"""
    eval_service = BenchmarkEvaluationService(db)
    failed = await eval_service.get_failed_cases(run_id)
    return {"total": len(failed), "items": failed}


# ============= 生成模板管理 =============

@router.get("/templates", response_model=GenerationTemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    domain: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取生成模板列表"""
    query = select(GenerationTemplate)
    
    if domain:
        query = query.where(GenerationTemplate.domain == domain)
    if is_active is not None:
        query = query.where(GenerationTemplate.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(GenerationTemplate.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return GenerationTemplateListResponse(total=total or 0, items=items)


@router.post("/templates", response_model=GenerationTemplateResponse)
async def create_template(
    data: GenerationTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建生成模板"""
    existing = await db.execute(
        select(GenerationTemplate).where(GenerationTemplate.template_code == data.template_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该模板编码已存在")
    
    template = GenerationTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.put("/templates/{template_id}", response_model=GenerationTemplateResponse)
async def update_template(
    template_id: int,
    data: GenerationTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新生成模板"""
    result = await db.execute(
        select(GenerationTemplate).where(GenerationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    
    return template


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除生成模板"""
    result = await db.execute(
        select(GenerationTemplate).where(GenerationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "删除成功"}


# ============= 辅助函数 =============

async def _update_dataset_case_count(db: AsyncSession, dataset_id: int):
    """更新数据集的用例统计"""
    # 统计各难度用例数
    result = await db.execute(
        select(BenchmarkCase.difficulty, func.count(BenchmarkCase.id))
        .where(BenchmarkCase.dataset_id == dataset_id, BenchmarkCase.is_active == True)
        .group_by(BenchmarkCase.difficulty)
    )
    rows = result.all()
    
    difficulty_dist = {}
    total = 0
    for diff, count in rows:
        diff_str = diff.value if diff else "unknown"
        difficulty_dist[diff_str] = count
        total += count
    
    # 更新数据集
    ds_result = await db.execute(
        select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
    )
    dataset = ds_result.scalar_one_or_none()
    if dataset:
        dataset.total_cases = total
        dataset.difficulty_distribution = difficulty_dist
        await db.commit()
