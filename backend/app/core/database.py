"""
GBSkillEngine 数据库连接管理
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """SQLAlchemy Base类"""
    pass


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 确保 PostgreSQL 枚举类型包含所有新增值
        # （create_all 不会修改已存在的枚举类型）
        try:
            await conn.execute(
                text("ALTER TYPE llmprovider ADD VALUE IF NOT EXISTS 'ZKH'")
            )
        except Exception:
            pass  # 枚举值已存在或类型尚未创建（首次启动时 create_all 已包含）


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
