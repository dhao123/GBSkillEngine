"""convert all enum columns to varchar

Revision ID: 006
Revises: 005
Create Date: 2024-02-14 12:00:00.000000

修复问题: PostgreSQL ENUM 类型 (llmprovider, skill_status, standard_status)
与 SQLAlchemy 的 SQLEnum 默认行为存在大小写不兼容:
- SQLAlchemy SQLEnum 默认用 enum .name (大写: OPENAI)
- 而数据库 ENUM 定义的是 .value (小写: openai)

彻底方案: 将所有 ENUM 列转为 VARCHAR，数据统一为小写，
彻底消除 PostgreSQL ENUM 类型的大小写映射问题。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === 1. llm_configs.provider: ENUM -> VARCHAR(50) ===
    # 先删除默认值（默认值可能引用 ENUM 类型），再转类型，再设新默认值
    op.execute("ALTER TABLE llm_configs ALTER COLUMN provider DROP DEFAULT")
    op.execute("""
        ALTER TABLE llm_configs 
        ALTER COLUMN provider TYPE varchar(50) USING provider::text
    """)
    op.execute("ALTER TABLE llm_configs ALTER COLUMN provider SET DEFAULT 'openai'")
    op.execute("""
        UPDATE llm_configs 
        SET provider = lower(provider) 
        WHERE provider != lower(provider)
    """)

    # 规范化 llm_usage_logs 表（该列本身是 varchar，只需规范数据）
    op.execute("""
        UPDATE llm_usage_logs 
        SET provider = lower(provider) 
        WHERE provider != lower(provider)
    """)

    # === 2. skills.status: ENUM -> VARCHAR(20) ===
    op.execute("ALTER TABLE skills ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE skills 
        ALTER COLUMN status TYPE varchar(20) USING status::text
    """)
    op.execute("ALTER TABLE skills ALTER COLUMN status SET DEFAULT 'draft'")
    op.execute("""
        UPDATE skills 
        SET status = lower(status) 
        WHERE status != lower(status)
    """)

    # === 3. standards.status: ENUM -> VARCHAR(20) ===
    op.execute("ALTER TABLE standards ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE standards 
        ALTER COLUMN status TYPE varchar(20) USING status::text
    """)
    op.execute("ALTER TABLE standards ALTER COLUMN status SET DEFAULT 'draft'")
    op.execute("""
        UPDATE standards 
        SET status = lower(status) 
        WHERE status != lower(status)
    """)

    # === 4. 删除不再需要的 PostgreSQL ENUM 类型 ===
    op.execute("DROP TYPE IF EXISTS llmprovider")
    op.execute("DROP TYPE IF EXISTS skill_status")
    op.execute("DROP TYPE IF EXISTS standard_status")


def downgrade() -> None:
    # 重建 ENUM 类型并恢复列类型
    op.execute("CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic', 'zkh', 'local')")
    op.execute("""
        ALTER TABLE llm_configs 
        ALTER COLUMN provider TYPE llmprovider USING provider::llmprovider
    """)

    op.execute("CREATE TYPE skill_status AS ENUM ('draft', 'testing', 'active', 'deprecated')")
    op.execute("""
        ALTER TABLE skills 
        ALTER COLUMN status TYPE skill_status USING status::skill_status
    """)

    op.execute("CREATE TYPE standard_status AS ENUM ('draft', 'uploaded', 'compiled', 'published', 'deprecated')")
    op.execute("""
        ALTER TABLE standards 
        ALTER COLUMN status TYPE standard_status USING status::standard_status
    """)
