"""
GBSkillEngine Skill编译器模块初始化
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.skill_compiler.compiler import SkillCompiler as MockSkillCompiler
from app.services.skill_compiler.llm_compiler import LLMSkillCompiler
from app.services.llm.base import BaseLLMProvider
from app.config import settings


class SkillCompilerFactory:
    """Skill编译器工厂"""
    
    @staticmethod
    def create(
        db: AsyncSession, 
        mode: Optional[str] = None,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        """
        创建编译器实例
        
        Args:
            db: 数据库会话
            mode: 编译模式 (mock/real)，默认使用配置
            llm_provider: LLM Provider实例（仅real模式需要）
            
        Returns:
            编译器实例
        """
        compile_mode = mode or settings.llm_mode
        
        if compile_mode == "real":
            return LLMSkillCompiler(db, llm_provider)
        else:
            return MockSkillCompiler(db)


# 保持向后兼容
SkillCompiler = MockSkillCompiler

__all__ = [
    "SkillCompiler",
    "MockSkillCompiler",
    "LLMSkillCompiler",
    "SkillCompilerFactory",
]
