"""
pytest 配置文件
"""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.models import Base


# 使用SQLite内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# 测试数据工厂
class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def standard_data(name: str = "GB/T 1234-2024") -> dict:
        """创建国标测试数据"""
        return {
            "name": name,
            "code": name.split()[0] if " " in name else name,
            "category": "机械",
            "status": "active"
        }
    
    @staticmethod
    def skill_data(skill_id: str = "SKILL_TEST_001") -> dict:
        """创建Skill测试数据"""
        return {
            "skill_id": skill_id,
            "name": "测试Skill",
            "version": "1.0.0",
            "standard_id": 1,
            "dsl_config": {
                "name": "测试Skill",
                "version": "1.0.0",
                "category": "测试",
                "attributes": [
                    {
                        "name": "test_attr",
                        "type": "string",
                        "required": True
                    }
                ],
                "rules": []
            },
            "status": "active"
        }
    
    @staticmethod
    def material_parse_data(material_name: str = "测试物料") -> dict:
        """创建物料梳理测试数据"""
        return {
            "material_name": material_name
        }


@pytest.fixture
def test_factory() -> TestDataFactory:
    """提供测试数据工厂"""
    return TestDataFactory()
