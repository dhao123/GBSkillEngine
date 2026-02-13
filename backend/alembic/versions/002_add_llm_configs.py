"""add llm_configs table

Revision ID: 002
Revises: 001
Create Date: 2024-02-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建LLM配置表
    op.create_table(
        'llm_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.Enum('openai', 'anthropic', 'baidu', 'aliyun', 'local', name='llmprovider'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('api_key_iv', sa.String(length=32), nullable=True),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('api_secret_iv', sa.String(length=32), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('temperature', sa.Float(), server_default='0.7', nullable=True),
        sa.Column('max_tokens', sa.Integer(), server_default='4096', nullable=True),
        sa.Column('timeout', sa.Integer(), server_default='60', nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='LLM配置表'
    )
    
    # 创建索引
    op.create_index('ix_llm_configs_id', 'llm_configs', ['id'], unique=False)
    op.create_index('ix_llm_configs_provider', 'llm_configs', ['provider'], unique=False)
    op.create_index('ix_llm_configs_is_default', 'llm_configs', ['is_default'], unique=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_llm_configs_is_default', table_name='llm_configs')
    op.drop_index('ix_llm_configs_provider', table_name='llm_configs')
    op.drop_index('ix_llm_configs_id', table_name='llm_configs')
    
    # 删除表
    op.drop_table('llm_configs')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS llmprovider')
