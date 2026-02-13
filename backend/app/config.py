"""
GBSkillEngine 配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    database_url: str = "postgresql+asyncpg://gbskill:gbskill123@localhost:5432/gbskillengine"
    
    # Neo4j配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j123"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 文件上传配置
    upload_dir: str = "./uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    
    # LLM配置
    llm_mode: str = "mock"  # mock 或 real
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4"
    llm_encryption_key: str = ""  # API Key加密密钥
    
    # 编译器配置
    compiler_max_retries: int = 3
    compiler_retry_delay: float = 1.0
    compiler_enable_cache: bool = True
    
    # CORS配置 - 存储为字符串，逗号分隔
    cors_origins_str: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    @property
    def cors_origins(self) -> List[str]:
        """解析CORS origins为列表"""
        return [origin.strip() for origin in self.cors_origins_str.split(',') if origin.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
