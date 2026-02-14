"""
GBSkillEngine OpenAI Provider实现
"""
import base64
import os
import time
from typing import Optional, Dict, Any, List
import logging

from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMConfig, LLMError

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT系列模型Provider"""
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    async def _create_client(self):
        """创建OpenAI客户端"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise LLMError(
                message="openai库未安装，请运行: pip install openai",
                provider=self.provider_name
            )
        
        client_kwargs = {"api_key": self.config.api_key}
        
        if self.config.endpoint:
            client_kwargs["base_url"] = self.config.endpoint
        
        if self.config.timeout:
            client_kwargs["timeout"] = self.config.timeout
        
        self._client = AsyncOpenAI(**client_kwargs)
        return self._client
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用OpenAI API"""
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
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
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
    
    async def generate_with_json_mode(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用OpenAI的JSON Mode生成结构化输出
        
        仅支持gpt-4-turbo和gpt-3.5-turbo-1106及以后版本
        """
        import json
        
        if not self._client:
            await self._create_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self._client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
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
        使用OpenAI视觉模型处理图片
        
        支持gpt-4o、gpt-4-turbo等视觉模型
        """
        if not self._client:
            await self._create_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 构建多模态content
        content_parts = [{"type": "text", "text": prompt}]
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                logger.warning(f"图片文件不存在，跳过: {img_path}")
                continue
            
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            # 检测MIME类型
            ext = os.path.splitext(img_path)[1].lower()
            mime_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}
            media_type = mime_map.get(ext, "jpeg")
            
            b64 = base64.b64encode(img_data).decode("utf-8")
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{media_type};base64,{b64}",
                    "detail": "high",
                }
            })
        
        if len(content_parts) == 1:
            # 没有有效图片，回退到纯文本
            logger.warning("无有效图片，回退到纯文本生成")
            return await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        messages.append({"role": "user", "content": content_parts})
        
        start_time = time.time()
        
        try:
            response = await self._client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )
            
            result_content = response.choices[0].message.content or ""
            
            return LLMResponse(
                content=result_content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                latency_ms=int((time.time() - start_time) * 1000),
                raw_response={
                    "id": response.id,
                    "created": response.created,
                    "finish_reason": response.choices[0].finish_reason,
                }
            )
        except Exception as e:
            raise LLMError(
                message=f"Vision API调用失败: {str(e)}",
                provider=self.provider_name,
                retryable=self._is_retryable_error(e)
            )
