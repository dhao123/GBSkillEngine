"""
GBSkillEngine Anthropic Provider实现
"""
from typing import Optional, Dict, Any, List
import logging

from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMConfig, LLMError

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude系列模型Provider"""
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    async def _create_client(self):
        """创建Anthropic客户端"""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise LLMError(
                message="anthropic库未安装，请运行: pip install anthropic",
                provider=self.provider_name
            )
        
        client_kwargs = {"api_key": self.config.api_key}
        
        if self.config.endpoint:
            client_kwargs["base_url"] = self.config.endpoint
        
        if self.config.timeout:
            client_kwargs["timeout"] = self.config.timeout
        
        self._client = AsyncAnthropic(**client_kwargs)
        return self._client
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用Anthropic API"""
        if not self._client:
            await self._create_client()
        
        # Anthropic格式: system单独传递，messages只包含user/assistant
        system_content = ""
        api_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                api_messages.append(msg)
        
        try:
            kwargs = {
                "model": self.config.model_name,
                "messages": api_messages,
                "max_tokens": max_tokens or self.config.max_tokens,
            }
            
            if system_content:
                kwargs["system"] = system_content
            
            if temperature is not None:
                kwargs["temperature"] = temperature
            
            response = await self._client.messages.create(**kwargs)
            
            # 提取文本内容
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                raw_response={
                    "id": response.id,
                    "stop_reason": response.stop_reason,
                }
            )
        except Exception as e:
            raise LLMError(
                message=str(e),
                provider=self.provider_name,
                retryable=self._is_retryable_error(e)
            )
