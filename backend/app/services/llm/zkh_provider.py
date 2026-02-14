"""
GBSkillEngine 震坤行(ZKH) Provider实现

ZKH大模型服务兼容OpenAI API格式，使用自定义端点。
支持文本推理和视觉理解两类模型。
"""
import base64
import os
import time
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
    
    async def generate_with_vision(
        self,
        prompt: str,
        image_paths: List[str],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        使用ZKH视觉理解模型处理图片
        
        ZKH视觉模型兼容OpenAI多模态消息格式，
        通过base64编码图片嵌入到content数组中。
        需要配置视觉能力的模型名称（如ZKH的视觉理解大模型）。
        """
        if not self._client:
            await self._create_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 构建多模态content (OpenAI兼容格式)
        content_parts = [{"type": "text", "text": prompt}]
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                logger.warning(f"图片文件不存在，跳过: {img_path}")
                continue
            
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            # 检测MIME类型
            ext = os.path.splitext(img_path)[1].lower()
            mime_map = {
                ".jpg": "jpeg", ".jpeg": "jpeg",
                ".png": "png", ".gif": "gif", ".webp": "webp",
            }
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
            # 没有有效图片，回退到纯文本推理
            logger.warning("无有效图片，回退到ZKH纯文本推理")
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
            
            # ZKH API可能不返回usage，做防御性处理
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return LLMResponse(
                content=result_content,
                model=response.model,
                usage=usage,
                latency_ms=int((time.time() - start_time) * 1000),
                raw_response={
                    "id": response.id,
                    "created": response.created,
                    "finish_reason": response.choices[0].finish_reason,
                }
            )
        except Exception as e:
            raise LLMError(
                message=f"ZKH Vision API调用失败: {str(e)}",
                provider=self.provider_name,
                retryable=self._is_retryable_error(e)
            )
