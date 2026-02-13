"""
GBSkillEngine 震坤行(ZKH) Provider实现

ZKH大模型服务兼容OpenAI API格式，使用自定义端点
"""
from typing import Optional, Dict, Any, List
import logging

from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMConfig, LLMError

logger = logging.getLogger(__name__)


class ZKHProvider(BaseLLMProvider):
    """震坤行大模型Provider (兼容OpenAI API)"""
    
    @property
    def provider_name(self) -> str:
        return "zkh"
    
    async def _create_client(self):
        """创建OpenAI兼容客户端"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise LLMError(
                message="openai库未安装，请运行: pip install openai",
                provider=self.provider_name
            )
        
        endpoint = self.config.endpoint or "https://ai.zkh.com/v1"
        
        self._client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=endpoint,
            timeout=self.config.timeout,
        )
        return self._client
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用ZKH API (OpenAI兼容格式)"""
        if not self._client:
            await self._create_client()
        
        try:
            response = await self._client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )
            
            content = response.choices[0].message.content or ""
            
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                raw_response={
                    "id": response.id,
                    "created": response.created,
                    "finish_reason": response.choices[0].finish_reason,
                }
            )
        except Exception as e:
            raise LLMError(
                message=str(e),
                provider=self.provider_name,
                retryable=self._is_retryable_error(e)
            )
