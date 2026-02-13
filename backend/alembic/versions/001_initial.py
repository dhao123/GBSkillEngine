"""Initial migration - create base tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create standards table
    op.create_table(
        'standards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('standard_code', sa.String(50), nullable=False, unique=True, index=True, comment='国标编号，如 GB/T 4219.1-2021'),
        sa.Column('standard_name', sa.String(200), nullable=False, comment='标准名称'),
        sa.Column('version_year', sa.String(10), nullable=True, comment='版本年份'),
        sa.Column('domain', sa.String(50), nullable=True, index=True, comment='适用领域：pipe/fastener/valve等'),
        sa.Column('product_scope', sa.Text(), nullable=True, comment='产品范围描述'),
        sa.Column('file_path', sa.String(500), nullable=True, comment='原始文件存储路径'),
        sa.Column('file_type', sa.String(10), nullable=True, comment='文件类型：pdf/doc/docx'),
        sa.Column('file_hash', sa.String(64), nullable=True, comment='文件SHA256哈希'),
        sa.Column('status', sa.Enum('draft', 'uploaded', 'compiled', 'published', name='standard_status'), 
                  nullable=False, server_default='draft', comment='状态'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), 
                  onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='国标管理表'
    )
    
    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('skill_id', sa.String(100), nullable=False, unique=True, index=True, comment='Skill唯一标识'),
        sa.Column('skill_name', sa.String(200), nullable=False, comment='Skill名称'),
        sa.Column('standard_id', sa.Integer(), nullable=True, comment='关联的国标ID'),
        sa.Column('domain', sa.String(50), nullable=True, index=True, comment='适用领域'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100', comment='优先级'),
        sa.Column('applicable_material_types', postgresql.JSONB(), nullable=True, comment='适用物料类型列表'),
        sa.Column('dsl_content', postgresql.JSONB(), nullable=False, comment='Skill DSL配置'),
        sa.Column('dsl_version', sa.String(20), nullable=False, server_default='1.0.0', comment='DSL版本号'),
        sa.Column('status', sa.Enum('draft', 'testing', 'active', 'deprecated', name='skill_status'),
                  nullable=False, server_default='draft', comment='状态'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['standard_id'], ['standards.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Skill管理表'
    )
    
    # Create skill_versions table
    op.create_table(
        'skill_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False, comment='关联的Skill ID'),
        sa.Column('version', sa.String(20), nullable=False, comment='版本号'),
        sa.Column('dsl_content', postgresql.JSONB(), nullable=False, comment='该版本的DSL配置'),
        sa.Column('change_log', sa.Text(), nullable=True, comment='变更说明'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false', comment='是否为当前激活版本'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Skill版本历史表'
    )
    op.create_index('ix_skill_versions_skill_id', 'skill_versions', ['skill_id'])
    
    # Create execution_logs table
    op.create_table(
        'execution_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trace_id', sa.String(36), nullable=False, unique=True, index=True, comment='追踪ID'),
        sa.Column('input_text', sa.Text(), nullable=False, comment='输入的原始物料描述'),
        sa.Column('matched_skills', postgresql.JSONB(), nullable=True, comment='匹配到的Skill ID列表'),
        sa.Column('executed_skill_id', sa.String(100), nullable=True, index=True, comment='实际执行的Skill ID'),
        sa.Column('execution_trace', postgresql.JSONB(), nullable=True, comment='执行Trace详情'),
        sa.Column('output_result', postgresql.JSONB(), nullable=True, comment='输出的结构化结果'),
        sa.Column('confidence_score', sa.Float(), nullable=True, comment='整体置信度'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='执行耗时(毫秒)'),
        sa.Column('status', sa.String(20), nullable=False, server_default='success', comment='执行状态'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, index=True),
        sa.PrimaryKeyConstraint('id'),
        comment='执行日志表'
    )


def downgrade() -> None:
    op.drop_table('execution_logs')
    op.drop_table('skill_versions')
    op.drop_table('skills')
    op.drop_table('standards')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS skill_status')
    op.execute('DROP TYPE IF EXISTS standard_status')
