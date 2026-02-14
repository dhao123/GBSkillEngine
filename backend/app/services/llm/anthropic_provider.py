"""
GBSkillEngine Anthropic Provider实现
"""
import base64
import os
import time
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
    
    async def generate_with_vision(
        self,
        prompt: str,
        image_paths: List[str],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        使用Anthropic Claude视觉模型处理图片
        
        支持claude-3-opus、claude-3-sonnet、claude-3-haiku、claude-3.5-sonnet等
        """
        if not self._client:
            await self._create_client()
        
        # 构建多模态content (Anthropic格式: image在前, text在后)
        content_parts = []
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                logger.warning(f"图片文件不存在，跳过: {img_path}")
                continue
            
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            # 检测MIME类型
            ext = os.path.splitext(img_path)[1].lower()
            mime_map = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
            }
            media_type = mime_map.get(ext, "image/jpeg")
            
            b64 = base64.b64encode(img_data).decode("utf-8")
            content_parts.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64,
                }
            })
        
        if not content_parts:
            # 没有有效图片，回退到纯文本
            logger.warning("无有效图片，回退到纯文本生成")
            return await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        # 文本部分放在图片之后
        content_parts.append({"type": "text", "text": prompt})
        
        start_time = time.time()
        
        try:
            kwargs = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": content_parts}],
                "max_tokens": max_tokens or self.config.max_tokens,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            if temperature is not None:
                kwargs["temperature"] = temperature
            
            response = await self._client.messages.create(**kwargs)
            
            # 提取文本内容
            result_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_content += block.text
            
            return LLMResponse(
                content=result_content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                latency_ms=int((time.time() - start_time) * 1000),
                raw_response={
                    "id": response.id,
                    "stop_reason": response.stop_reason,
                }
            )
        except Exception as e:
            raise LLMError(
                message=f"Vision API调用失败: {str(e)}",
                provider=self.provider_name,
                retryable=self._is_retryable_error(e)
            )
