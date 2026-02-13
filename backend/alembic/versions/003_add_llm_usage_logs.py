"""add llm_usage_logs table and zkh provider

Revision ID: 003
Revises: 002
Create Date: 2024-02-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建LLM使用记录表
    op.create_table(
        'llm_usage_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('caller', sa.String(length=100), nullable=True),
        sa.Column('prompt_preview', sa.String(length=500), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), server_default='0', nullable=True),
        sa.Column('completion_tokens', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=True),
        sa.Column('latency_ms', sa.Integer(), server_default='0', nullable=True),
        sa.Column('success', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='LLM调用记录表'
    )

    op.create_index('ix_llm_usage_logs_id', 'llm_usage_logs', ['id'])
    op.create_index('ix_llm_usage_logs_config_id', 'llm_usage_logs', ['config_id'])
    op.create_index('ix_llm_usage_logs_provider', 'llm_usage_logs', ['provider'])
    op.create_index('ix_llm_usage_logs_model_name', 'llm_usage_logs', ['model_name'])
    op.create_index('ix_llm_usage_logs_created_at', 'llm_usage_logs', ['created_at'])

    # 扩展 llmprovider 枚举，增加 ZKH 值
    # PostgreSQL 枚举类型需要使用 ALTER TYPE
    # 注意：SQLAlchemy 对 PEP 435 枚举默认使用 .name（大写），非 .value
    op.execute("ALTER TYPE llmprovider ADD VALUE IF NOT EXISTS 'ZKH'")


def downgrade() -> None:
    op.drop_index('ix_llm_usage_logs_created_at', table_name='llm_usage_logs')
    op.drop_index('ix_llm_usage_logs_model_name', table_name='llm_usage_logs')
    op.drop_index('ix_llm_usage_logs_provider', table_name='llm_usage_logs')
    op.drop_index('ix_llm_usage_logs_config_id', table_name='llm_usage_logs')
    op.drop_index('ix_llm_usage_logs_id', table_name='llm_usage_logs')
    op.drop_table('llm_usage_logs')
    # 注意: PostgreSQL 不支持从枚举类型中移除值
