"""
GBSkillEngine LLM Provider工厂

根据配置创建对应的Provider实例
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.services.llm.base import BaseLLMProvider, LLMConfig as ProviderConfig, LLMError
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.local_provider import LocalProvider
from app.services.llm.zkh_provider import ZKHProvider
from app.models.llm_config import LLMConfig, LLMProvider
from app.utils.encryption import decrypt_api_key

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """LLM Provider工厂类"""
    
    # 供应商到Provider类的映射
    _provider_map = {
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.ANTHROPIC: AnthropicProvider,
        LLMProvider.ZKH: ZKHProvider,
        LLMProvider.LOCAL: LocalProvider,
    }
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMProvider:
        """
        根据配置创建Provider实例
        
        Args:
            config: 数据库LLMConfig模型实例
            
        Returns:
            BaseLLMProvider实例
        """
        provider_class = cls._provider_map.get(config.provider)
        
        if not provider_class:
            raise LLMError(
                message=f"不支持的供应商: {config.provider.value}",
                provider=config.provider.value
            )
        
        # 解密API Key
        api_key = ""
        if config.api_key_encrypted and config.api_key_iv:
            try:
                api_key = decrypt_api_key(config.api_key_encrypted, config.api_key_iv)
            except Exception as e:
                raise LLMError(
                    message=f"API Key解密失败: {str(e)}",
                    provider=config.provider.value
                )
        
        # 解密API Secret (如果有)
        api_secret = None
        if config.api_secret_encrypted and config.api_secret_iv:
            try:
                api_secret = decrypt_api_key(config.api_secret_encrypted, config.api_secret_iv)
            except Exception:
                pass
        
        # 创建Provider配置
        provider_config = ProviderConfig(
            provider=config.provider.value,
            api_key=api_key,
            api_secret=api_secret,
            model_name=config.model_name,
            endpoint=config.endpoint,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
        )
        
        return provider_class(provider_config)
    
    @classmethod
    def create_from_dict(cls, config_dict: dict) -> BaseLLMProvider:
        """
        从字典创建Provider实例
        
        Args:
            config_dict: 配置字典，包含provider, api_key, model_name等
            
        Returns:
            BaseLLMProvider实例
        """
        provider_value = config_dict.get("provider", "openai")
        
        # 转换字符串到枚举
        try:
            provider_enum = LLMProvider(provider_value)
        except ValueError:
            raise LLMError(
                message=f"不支持的供应商: {provider_value}",
                provider=provider_value
            )
        
        provider_class = cls._provider_map.get(provider_enum)
        
        if not provider_class:
            raise LLMError(
                message=f"不支持的供应商: {provider_value}",
                provider=provider_value
            )
        
        provider_config = ProviderConfig(
            provider=provider_value,
            api_key=config_dict.get("api_key", ""),
            api_secret=config_dict.get("api_secret"),
            model_name=config_dict.get("model_name", "gpt-4"),
            endpoint=config_dict.get("endpoint"),
            temperature=config_dict.get("temperature", 0.7),
            max_tokens=config_dict.get("max_tokens", 4096),
            timeout=config_dict.get("timeout", 60),
        )
        
        return provider_class(provider_config)
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """获取支持的供应商列表"""
        return list(cls._provider_map.keys())


async def get_default_provider(db: AsyncSession) -> Optional[BaseLLMProvider]:
    """
    获取默认的LLM Provider
    
    Args:
        db: 数据库会话
        
    Returns:
        默认Provider实例，如果没有配置返回None
    """
    result = await db.execute(
        select(LLMConfig).where(
            LLMConfig.is_default == True,
            LLMConfig.is_active == True
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        # 尝试获取任意一个激活的配置
        result = await db.execute(
            select(LLMConfig).where(LLMConfig.is_active == True).limit(1)
        )
        config = result.scalar_one_or_none()
    
    if config:
        return LLMProviderFactory.create(config)
    
    return None


async def get_provider_by_id(db: AsyncSession, config_id: int) -> Optional[BaseLLMProvider]:
    """
    根据配置ID获取Provider
    
    Args:
        db: 数据库会话
        config_id: 配置ID
        
    Returns:
        Provider实例，如果不存在返回None
    """
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if config:
        return LLMProviderFactory.create(config)
    
    return None
