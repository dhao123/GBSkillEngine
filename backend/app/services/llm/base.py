"""
GBSkillEngine LLM Provider抽象基类

使用Strategy模式实现多供应商支持
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import time
import logging

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM调用错误"""
    def __init__(self, message: str, provider: str = "", retryable: bool = False):
        self.message = message
        self.provider = provider
        self.retryable = retryable
        super().__init__(message)


@dataclass
class LLMResponse:
    """LLM响应数据结构"""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0
    raw_response: Optional[Dict[str, Any]] = None
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)
    
    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)


@dataclass
class LLMConfig:
    """LLM配置数据"""
    provider: str
    api_key: str
    model_name: str
    api_secret: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


class BaseLLMProvider(ABC):
    """
    LLM Provider抽象基类
    
    所有供应商实现都应继承此类
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """供应商名称"""
        pass
    
    @abstractmethod
    async def _create_client(self):
        """创建API客户端"""
        pass
    
    @abstractmethod
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用API"""
        pass
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        生成文本
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数 (覆盖配置)
            max_tokens: 最大Token数 (覆盖配置)
            
        Returns:
            LLMResponse: 生成结果
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        try:
            response = await self._call_api(
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )
            response.latency_ms = int((time.time() - start_time) * 1000)
            return response
        except Exception as e:
            logger.error(f"LLM调用失败 [{self.provider_name}]: {str(e)}")
            raise LLMError(
                message=str(e),
                provider=self.provider_name,
                retryable=self._is_retryable_error(e)
            )
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成JSON格式输出
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            json_schema: JSON Schema约束 (部分供应商支持)
            
        Returns:
            解析后的JSON对象
        """
        import json
        
        # 在system prompt中强调JSON输出
        enhanced_system = system_prompt or ""
        enhanced_system += "\n\n请确保输出是有效的JSON格式，不要包含任何额外的文本或标记。"
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=enhanced_system,
        )
        
        # 尝试解析JSON
        content = response.content.strip()
        
        # 移除可能的markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {str(e)}, 原始内容: {content[:200]}...")
            raise LLMError(
                message=f"JSON解析失败: {str(e)}",
                provider=self.provider_name,
                retryable=True
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
        多模态生成(文本+图片)
        
        Args:
            prompt: 用户提示词
            image_paths: 图片文件路径列表
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大Token数
            
        Returns:
            LLMResponse: 生成结果
            
        Raises:
            NotImplementedError: 如果Provider不支持视觉能力
        """
        raise NotImplementedError(
            f"{self.provider_name} 不支持视觉能力"
        )
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_str = str(error).lower()
        retryable_keywords = [
            "rate limit",
            "timeout",
            "connection",
            "temporary",
            "overloaded",
            "503",
            "502",
            "429",
        ]
        return any(kw in error_str for kw in retryable_keywords)
