"""
GBSkillEngine 本地模型 Provider实现

支持Ollama和其他兼容OpenAI API的本地模型服务
"""
from typing import Optional, Dict, Any, List
import logging
import httpx

from app.services.llm.base import BaseLLMProvider, LLMResponse, LLMConfig, LLMError

logger = logging.getLogger(__name__)


class LocalProvider(BaseLLMProvider):
    """本地模型Provider (Ollama/vLLM等)"""
    
    @property
    def provider_name(self) -> str:
        return "local"
    
    async def _create_client(self):
        """创建HTTP客户端"""
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用本地模型API"""
        if not self._client:
            await self._create_client()
        
        base_url = self.config.endpoint or "http://localhost:11434"
        
        # 尝试OpenAI兼容格式
        try:
            return await self._call_openai_compatible(
                base_url, messages, temperature, max_tokens
            )
        except Exception as e:
            logger.debug(f"OpenAI兼容API失败，尝试Ollama原生API: {e}")
        
        # 回退到Ollama原生格式
        return await self._call_ollama_native(
            base_url, messages, temperature, max_tokens
        )
    
    async def _call_openai_compatible(
        self,
        base_url: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """调用OpenAI兼容API (vLLM, Ollama的OpenAI兼容端点)"""
        url = f"{base_url}/v1/chat/completions"
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        
        response = await self._client.post(url, json=payload)
        
        if response.status_code != 200:
            raise LLMError(
                message=f"API错误: {response.status_code} - {response.text}",
                provider=self.provider_name
            )
        
        data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model=data.get("model", self.config.model_name),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw_response=data
        )
    
    async def _call_ollama_native(
        self,
        base_url: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> LLMResponse:
        """调用Ollama原生API"""
        url = f"{base_url}/api/chat"
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
            }
        }
        
        response = await self._client.post(url, json=payload)
        
        if response.status_code != 200:
            raise LLMError(
                message=f"Ollama API错误: {response.status_code} - {response.text}",
                provider=self.provider_name
            )
        
        data = response.json()
        
        content = data.get("message", {}).get("content", "")
        
        return LLMResponse(
            content=content,
            model=data.get("model", self.config.model_name),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
            raw_response=data
        )
    
    async def list_models(self) -> List[str]:
        """获取本地可用模型列表"""
        if not self._client:
            await self._create_client()
        
        base_url = self.config.endpoint or "http://localhost:11434"
        url = f"{base_url}/api/tags"
        
        try:
            response = await self._client.get(url)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"获取本地模型列表失败: {e}")
        
        return []
