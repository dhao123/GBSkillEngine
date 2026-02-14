"""
GBSkillEngine Settings API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func as sa_func, case, cast, Float
from typing import List
import time
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.llm_config import LLMConfig, LLMProvider, LLM_PROVIDER_INFO
from app.models.llm_usage_log import LLMUsageLog
from app.schemas.settings import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    LLMConfigListResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
    LLMProviderInfo,
    LLMProviderListResponse,
    SystemInfo,
    SuccessResponse,
    LLMUsageLogResponse,
    LLMUsageLogListResponse,
    UsageTrendPoint,
    UsageSummary,
    UsageMonitorResponse,
)
from app.utils.encryption import encrypt_api_key, decrypt_api_key, mask_api_key
from app.config import settings

router = APIRouter(prefix="/settings", tags=["系统配置"])
logger = logging.getLogger(__name__)


def _config_to_response(config: LLMConfig) -> LLMConfigResponse:
    """将数据库模型转换为响应Schema"""
    # 解密并脱敏API Key
    api_key_masked = ""
    if config.api_key_encrypted and config.api_key_iv:
        try:
            plain_key = decrypt_api_key(config.api_key_encrypted, config.api_key_iv)
            api_key_masked = mask_api_key(plain_key)
        except Exception:
            api_key_masked = "****"
    
    return LLMConfigResponse(
        id=config.id,
        provider=config.provider,
        name=config.name,
        model_name=config.model_name,
        endpoint=config.endpoint,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout,
        api_key_masked=api_key_masked,
        has_api_secret=bool(config.api_secret_encrypted),
        is_default=config.is_default,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ==================== LLM配置 CRUD ====================

@router.get("/llm-configs", response_model=LLMConfigListResponse)
async def list_llm_configs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取LLM配置列表"""
    # 统计总数
    count_result = await db.execute(select(LLMConfig))
    all_configs = count_result.scalars().all()
    total = len(all_configs)
    
    # 分页查询
    result = await db.execute(
        select(LLMConfig)
        .order_by(LLMConfig.is_default.desc(), LLMConfig.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    configs = result.scalars().all()
    
    return LLMConfigListResponse(
        total=total,
        items=[_config_to_response(c) for c in configs]
    )


@router.get("/llm-configs/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取单个LLM配置详情"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM配置 {config_id} 不存在"
        )
    
    return _config_to_response(config)


@router.post("/llm-configs", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    data: LLMConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建LLM配置"""
    # 加密API Key
    api_key_encrypted, api_key_iv = encrypt_api_key(data.api_key)
    
    # 加密API Secret (如果有)
    api_secret_encrypted = None
    api_secret_iv = None
    if data.api_secret:
        api_secret_encrypted, api_secret_iv = encrypt_api_key(data.api_secret)
    
    # 如果设为默认，先取消其他默认配置
    if data.is_default:
        await db.execute(
            update(LLMConfig).values(is_default=False)
        )
    
    # 创建配置
    config = LLMConfig(
        provider=data.provider,
        name=data.name,
        model_name=data.model_name,
        endpoint=data.endpoint,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        timeout=data.timeout,
        api_key_encrypted=api_key_encrypted,
        api_key_iv=api_key_iv,
        api_secret_encrypted=api_secret_encrypted,
        api_secret_iv=api_secret_iv,
        is_default=data.is_default,
        is_active=True,
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    logger.info(f"创建LLM配置: {config.name} ({config.provider.value})")
    
    return _config_to_response(config)


@router.put("/llm-configs/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: int,
    data: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM配置 {config_id} 不存在"
        )
    
    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    
    # 处理API Key更新
    if 'api_key' in update_data and update_data['api_key']:
        api_key_encrypted, api_key_iv = encrypt_api_key(update_data['api_key'])
        config.api_key_encrypted = api_key_encrypted
        config.api_key_iv = api_key_iv
        del update_data['api_key']
    elif 'api_key' in update_data:
        del update_data['api_key']
    
    # 处理API Secret更新
    if 'api_secret' in update_data and update_data['api_secret']:
        api_secret_encrypted, api_secret_iv = encrypt_api_key(update_data['api_secret'])
        config.api_secret_encrypted = api_secret_encrypted
        config.api_secret_iv = api_secret_iv
        del update_data['api_secret']
    elif 'api_secret' in update_data:
        del update_data['api_secret']
    
    # 更新其他字段
    for key, value in update_data.items():
        setattr(config, key, value)
    
    await db.commit()
    await db.refresh(config)
    
    logger.info(f"更新LLM配置: {config.name}")
    
    return _config_to_response(config)


@router.delete("/llm-configs/{config_id}", response_model=SuccessResponse)
async def delete_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM配置 {config_id} 不存在"
        )
    
    config_name = config.name
    await db.delete(config)
    await db.commit()
    
    logger.info(f"删除LLM配置: {config_name}")
    
    return SuccessResponse(message=f"已删除配置: {config_name}")


# ==================== 连接测试 ====================

@router.post("/llm-configs/{config_id}/test", response_model=ConnectionTestResponse)
async def test_llm_connection(
    config_id: int,
    request: ConnectionTestRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """测试LLM连接"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM配置 {config_id} 不存在"
        )
    
    # 解密API Key
    try:
        api_key = decrypt_api_key(config.api_key_encrypted, config.api_key_iv)
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"API Key解密失败: {str(e)}"
        )
    
    # 解密API Secret (如果有)
    api_secret = None
    if config.api_secret_encrypted and config.api_secret_iv:
        try:
            api_secret = decrypt_api_key(config.api_secret_encrypted, config.api_secret_iv)
        except Exception:
            pass
    
    # 执行连接测试
    start_time = time.time()
    test_result = await _test_provider_connection(
        provider=config.provider,
        api_key=api_key,
        api_secret=api_secret,
        model_name=config.model_name,
        endpoint=config.endpoint,
        test_prompt=request.test_prompt if request else "Hello"
    )
    latency_ms = int((time.time() - start_time) * 1000)
    
    test_result.latency_ms = latency_ms
    return test_result


async def _test_provider_connection(
    provider: LLMProvider,
    api_key: str,
    api_secret: str | None,
    model_name: str,
    endpoint: str | None,
    test_prompt: str
) -> ConnectionTestResponse:
    """测试特定供应商的连接"""
    try:
        if provider == LLMProvider.OPENAI:
            return await _test_openai(api_key, model_name, endpoint, test_prompt)
        elif provider == LLMProvider.ANTHROPIC:
            return await _test_anthropic(api_key, model_name, endpoint, test_prompt)
        # elif provider == LLMProvider.BAIDU:
        #     return await _test_baidu(api_key, api_secret, model_name, test_prompt)
        # elif provider == LLMProvider.ALIYUN:
        #     return await _test_aliyun(api_key, model_name, test_prompt)
        elif provider == LLMProvider.ZKH:
            return await _test_zkh(api_key, model_name, endpoint, test_prompt)
        elif provider == LLMProvider.LOCAL:
            return await _test_local(endpoint, model_name, test_prompt)
        else:
            return ConnectionTestResponse(
                success=False,
                message=f"不支持的供应商: {provider.value}"
            )
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        return ConnectionTestResponse(
            success=False,
            message=f"连接测试失败: {str(e)}"
        )


async def _test_openai(api_key: str, model: str, endpoint: str | None, prompt: str) -> ConnectionTestResponse:
    """测试OpenAI连接"""
    try:
        from openai import AsyncOpenAI
        
        client_kwargs = {"api_key": api_key}
        if endpoint:
            client_kwargs["base_url"] = endpoint
        
        client = AsyncOpenAI(**client_kwargs)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        
        return ConnectionTestResponse(
            success=True,
            message="连接成功",
            model_info={
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }
            }
        )
    except ImportError:
        return ConnectionTestResponse(
            success=False,
            message="openai库未安装，请安装: pip install openai"
        )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"OpenAI连接失败: {str(e)}"
        )


async def _test_anthropic(api_key: str, model: str, endpoint: str | None, prompt: str) -> ConnectionTestResponse:
    """测试Anthropic连接"""
    try:
        from anthropic import AsyncAnthropic
        
        client_kwargs = {"api_key": api_key}
        if endpoint:
            client_kwargs["base_url"] = endpoint
        
        client = AsyncAnthropic(**client_kwargs)
        
        response = await client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return ConnectionTestResponse(
            success=True,
            message="连接成功",
            model_info={
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            }
        )
    except ImportError:
        return ConnectionTestResponse(
            success=False,
            message="anthropic库未安装，请安装: pip install anthropic"
        )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"Anthropic连接失败: {str(e)}"
        )


async def _test_baidu(api_key: str, api_secret: str | None, model: str, prompt: str) -> ConnectionTestResponse:
    """测试百度文心连接"""
    try:
        import httpx
        
        if not api_secret:
            return ConnectionTestResponse(
                success=False,
                message="百度文心需要配置API Secret"
            )
        
        # 获取access_token
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={api_secret}"
        
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(token_url)
            token_data = token_resp.json()
            
            if "access_token" not in token_data:
                return ConnectionTestResponse(
                    success=False,
                    message=f"获取access_token失败: {token_data.get('error_description', '未知错误')}"
                )
            
            access_token = token_data["access_token"]
            
            # 调用模型
            model_map = {
                "ernie-4.0-8k": "completions_pro",
                "ernie-3.5-8k": "completions",
                "ernie-speed-128k": "ernie_speed",
            }
            model_endpoint = model_map.get(model, "completions")
            
            chat_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model_endpoint}?access_token={access_token}"
            
            chat_resp = await client.post(
                chat_url,
                json={"messages": [{"role": "user", "content": prompt}]}
            )
            chat_data = chat_resp.json()
            
            if "error_code" in chat_data:
                return ConnectionTestResponse(
                    success=False,
                    message=f"调用失败: {chat_data.get('error_msg', '未知错误')}"
                )
            
            return ConnectionTestResponse(
                success=True,
                message="连接成功",
                model_info={
                    "model": model,
                    "usage": chat_data.get("usage", {})
                }
            )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"百度文心连接失败: {str(e)}"
        )


async def _test_aliyun(api_key: str, model: str, prompt: str) -> ConnectionTestResponse:
    """测试阿里通义连接"""
    try:
        import httpx
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": {"messages": [{"role": "user", "content": prompt}]},
                    "parameters": {"max_tokens": 50}
                }
            )
            data = response.json()
            
            if "output" in data:
                return ConnectionTestResponse(
                    success=True,
                    message="连接成功",
                    model_info={
                        "model": model,
                        "usage": data.get("usage", {})
                    }
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"调用失败: {data.get('message', '未知错误')}"
                )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"阿里通义连接失败: {str(e)}"
        )


async def _test_local(endpoint: str | None, model: str, prompt: str) -> ConnectionTestResponse:
    """测试本地模型连接 (Ollama格式)"""
    try:
        import httpx
        
        base_url = endpoint or "http://localhost:11434"
        url = f"{base_url}/api/generate"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return ConnectionTestResponse(
                    success=True,
                    message="连接成功",
                    model_info={
                        "model": data.get("model", model),
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration")
                    }
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"本地模型响应错误: {response.status_code}"
                )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"本地模型连接失败: {str(e)}"
        )


async def _test_zkh(api_key: str, model: str, endpoint: str | None, prompt: str) -> ConnectionTestResponse:
    """测试震坤行大模型连接 (兼容OpenAI API)"""
    try:
        from openai import AsyncOpenAI
        
        base_url = endpoint or "https://ai.zkh.com/v1"
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        
        usage_info = {}
        if response.usage:
            usage_info = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
        
        return ConnectionTestResponse(
            success=True,
            message="连接成功",
            model_info={"model": response.model, "usage": usage_info}
        )
    except ImportError:
        return ConnectionTestResponse(
            success=False,
            message="openai库未安装，请安装: pip install openai"
        )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"震坤行连接失败: {str(e)}"
        )


# ==================== 设为默认 ====================

@router.put("/llm-configs/{config_id}/set-default", response_model=LLMConfigResponse)
async def set_default_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """设置默认LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM配置 {config_id} 不存在"
        )
    
    # 取消其他默认配置
    await db.execute(
        update(LLMConfig).values(is_default=False)
    )
    
    # 设置当前配置为默认
    config.is_default = True
    await db.commit()
    await db.refresh(config)
    
    logger.info(f"设置默认LLM配置: {config.name}")
    
    return _config_to_response(config)


# ==================== 供应商信息 ====================

@router.get("/providers", response_model=LLMProviderListResponse)
async def list_llm_providers():
    """获取支持的LLM供应商列表"""
    providers = []
    for provider, info in LLM_PROVIDER_INFO.items():
        providers.append(LLMProviderInfo(
            provider=provider,
            name=info["name"],
            description=info["description"],
            models=info["models"],
            default_endpoint=info["default_endpoint"],
            requires_secret=info["requires_secret"],
            supports_custom_endpoint=info["supports_custom_endpoint"],
        ))
    
    return LLMProviderListResponse(providers=providers)


# ==================== 系统信息 ====================

@router.get("/system-info", response_model=SystemInfo)
async def get_system_info(db: AsyncSession = Depends(get_db)):
    """获取系统配置信息"""
    # 查询默认配置
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_default == True)
    )
    default_config = result.scalar_one_or_none()
    
    return SystemInfo(
        version="1.0.0",
        llm_mode=settings.llm_mode,
        default_llm_config_id=default_config.id if default_config else None,
        default_llm_provider=default_config.provider.value if default_config else None,
        default_llm_model=default_config.model_name if default_config else None,
    )


# ==================== LLM使用监控 ====================

@router.get("/llm-usage/monitor", response_model=UsageMonitorResponse)
async def get_usage_monitor(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    provider: str | None = Query(None, description="按供应商过滤"),
    db: AsyncSession = Depends(get_db)
):
    """获取LLM使用监控数据（汇总+趋势）"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 构建基础过滤条件
    base_filter = [LLMUsageLog.created_at >= start_date]
    if provider:
        base_filter.append(LLMUsageLog.provider == provider)
    
    # === 汇总统计 ===
    summary_query = select(
        sa_func.count(LLMUsageLog.id).label("total_calls"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.prompt_tokens), 0).label("total_prompt_tokens"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.completion_tokens), 0).label("total_completion_tokens"),
        sa_func.coalesce(sa_func.avg(LLMUsageLog.latency_ms), 0).label("avg_latency_ms"),
        sa_func.sum(case((LLMUsageLog.success == True, 1), else_=0)).label("success_calls"),
    ).where(*base_filter)
    
    summary_result = (await db.execute(summary_query)).one()
    
    total_calls = summary_result.total_calls or 0
    success_calls = summary_result.success_calls or 0
    
    summary = UsageSummary(
        total_calls=total_calls,
        total_tokens=summary_result.total_tokens,
        total_prompt_tokens=summary_result.total_prompt_tokens,
        total_completion_tokens=summary_result.total_completion_tokens,
        avg_latency_ms=round(float(summary_result.avg_latency_ms), 1),
        success_rate=round(success_calls / total_calls, 4) if total_calls > 0 else 0,
    )
    
    # 按供应商汇总
    provider_query = select(
        LLMUsageLog.provider,
        sa_func.count(LLMUsageLog.id).label("calls"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.total_tokens), 0).label("tokens"),
    ).where(*base_filter).group_by(LLMUsageLog.provider)
    
    provider_rows = (await db.execute(provider_query)).all()
    summary.by_provider = {
        row.provider: {"calls": row.calls, "tokens": row.tokens}
        for row in provider_rows
    }
    
    # 按模型汇总
    model_query = select(
        LLMUsageLog.model_name,
        sa_func.count(LLMUsageLog.id).label("calls"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.total_tokens), 0).label("tokens"),
    ).where(*base_filter).group_by(LLMUsageLog.model_name)
    
    model_rows = (await db.execute(model_query)).all()
    summary.by_model = {
        row.model_name: {"calls": row.calls, "tokens": row.tokens}
        for row in model_rows
    }
    
    # === 每日趋势 ===
    date_trunc = sa_func.date_trunc('day', LLMUsageLog.created_at)
    
    trend_query = select(
        date_trunc.label("day"),
        sa_func.count(LLMUsageLog.id).label("total_calls"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.prompt_tokens), 0).label("prompt_tokens"),
        sa_func.coalesce(sa_func.sum(LLMUsageLog.completion_tokens), 0).label("completion_tokens"),
        sa_func.sum(case((LLMUsageLog.success == True, 1), else_=0)).label("success_calls"),
        sa_func.sum(case((LLMUsageLog.success == False, 1), else_=0)).label("failed_calls"),
        sa_func.coalesce(sa_func.avg(LLMUsageLog.latency_ms), 0).label("avg_latency_ms"),
    ).where(*base_filter).group_by(date_trunc).order_by(date_trunc)
    
    trend_rows = (await db.execute(trend_query)).all()
    
    trend = [
        UsageTrendPoint(
            date=row.day.strftime("%Y-%m-%d"),
            total_tokens=row.total_tokens,
            prompt_tokens=row.prompt_tokens,
            completion_tokens=row.completion_tokens,
            total_calls=row.total_calls,
            success_calls=row.success_calls or 0,
            failed_calls=row.failed_calls or 0,
            avg_latency_ms=round(float(row.avg_latency_ms), 1),
        )
        for row in trend_rows
    ]
    
    return UsageMonitorResponse(summary=summary, trend=trend)


@router.get("/llm-usage/logs", response_model=LLMUsageLogListResponse)
async def list_usage_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    provider: str | None = Query(None),
    success: bool | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取LLM调用记录列表"""
    filters = []
    if provider:
        filters.append(LLMUsageLog.provider == provider)
    if success is not None:
        filters.append(LLMUsageLog.success == success)
    
    # 总数
    count_q = select(sa_func.count(LLMUsageLog.id)).where(*filters) if filters else select(sa_func.count(LLMUsageLog.id))
    total = (await db.execute(count_q)).scalar() or 0
    
    # 分页
    query = (
        select(LLMUsageLog)
        .order_by(LLMUsageLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if filters:
        query = query.where(*filters)
    
    rows = (await db.execute(query)).scalars().all()
    
    return LLMUsageLogListResponse(
        total=total,
        items=[LLMUsageLogResponse.model_validate(r) for r in rows]
    )
