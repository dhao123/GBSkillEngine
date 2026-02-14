"""Add benchmark evaluation system tables

Revision ID: 005
Revises: 004
Create Date: 2026-02-14

This migration adds the following tables for the benchmark evaluation system:
- benchmark_datasets: 评测数据集元数据
- benchmark_cases: 测试用例
- benchmark_runs: 评测运行记录
- benchmark_results: 评测结果
- generation_templates: 数据生成模板
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 创建 benchmark_datasets 表
    op.create_table(
        'benchmark_datasets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_code', sa.String(100), nullable=False, comment='数据集唯一编码'),
        sa.Column('dataset_name', sa.String(500), nullable=False, comment='数据集名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('skill_id', sa.Integer(), nullable=True, comment='关联的Skill ID'),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='mixed', 
                  comment='来源类型: seed/generated/mixed'),
        sa.Column('difficulty_distribution', sa.JSON(), nullable=True,
                  comment='难度分布 {"easy": 40, "medium": 30, "hard": 20, "adversarial": 10}'),
        sa.Column('total_cases', sa.Integer(), nullable=False, server_default='0', comment='总用例数'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft',
                  comment='状态: draft/ready/archived'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                  onupdate=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True, comment='创建人'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='SET NULL'),
        comment='Benchmark评测数据集'
    )
    op.create_index('ix_benchmark_datasets_id', 'benchmark_datasets', ['id'])
    op.create_index('ix_benchmark_datasets_code', 'benchmark_datasets', ['dataset_code'], unique=True)
    op.create_index('ix_benchmark_datasets_status', 'benchmark_datasets', ['status'])

    # 2. 创建 benchmark_cases 表
    op.create_table(
        'benchmark_cases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False, comment='所属数据集ID'),
        sa.Column('case_code', sa.String(100), nullable=False, comment='用例编码'),
        sa.Column('input_text', sa.Text(), nullable=False, comment='输入文本(物料描述)'),
        sa.Column('expected_skill_id', sa.String(200), nullable=True, comment='期望匹配的Skill ID'),
        sa.Column('expected_attributes', sa.JSON(), nullable=False, 
                  comment='期望输出属性 {"公称直径": {"value": 100, "unit": "mm"}, ...}'),
        sa.Column('expected_category', sa.JSON(), nullable=True, comment='期望类目映射'),
        sa.Column('difficulty', sa.String(50), nullable=False, server_default='medium',
                  comment='难度: easy/medium/hard/adversarial'),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='seed',
                  comment='来源: seed/table_enum/template/noise'),
        sa.Column('source_reference', sa.JSON(), nullable=True, 
                  comment='来源追溯 {"table": "dimension_table", "row_index": 5}'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签数组'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dataset_id'], ['benchmark_datasets.id'], ondelete='CASCADE'),
        comment='Benchmark测试用例'
    )
    op.create_index('ix_benchmark_cases_id', 'benchmark_cases', ['id'])
    op.create_index('ix_benchmark_cases_dataset_id', 'benchmark_cases', ['dataset_id'])
    op.create_index('ix_benchmark_cases_difficulty', 'benchmark_cases', ['difficulty'])
    op.create_index('ix_benchmark_cases_code', 'benchmark_cases', ['case_code'])

    # 3. 创建 benchmark_runs 表
    op.create_table(
        'benchmark_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_code', sa.String(100), nullable=False, comment='评测运行编码'),
        sa.Column('dataset_id', sa.Integer(), nullable=False, comment='使用的数据集ID'),
        sa.Column('run_name', sa.String(500), nullable=True, comment='运行名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('config', sa.JSON(), nullable=True, 
                  comment='运行配置 {"tolerance": 0.05, "partial_match": true}'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending',
                  comment='状态: pending/running/completed/failed'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('total_cases', sa.Integer(), nullable=False, server_default='0', comment='总用例数'),
        sa.Column('completed_cases', sa.Integer(), nullable=False, server_default='0', comment='已完成用例数'),
        sa.Column('metrics', sa.JSON(), nullable=True, comment='汇总指标'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True, comment='创建人'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dataset_id'], ['benchmark_datasets.id'], ondelete='CASCADE'),
        comment='Benchmark评测运行记录'
    )
    op.create_index('ix_benchmark_runs_id', 'benchmark_runs', ['id'])
    op.create_index('ix_benchmark_runs_code', 'benchmark_runs', ['run_code'], unique=True)
    op.create_index('ix_benchmark_runs_dataset_id', 'benchmark_runs', ['dataset_id'])
    op.create_index('ix_benchmark_runs_status', 'benchmark_runs', ['status'])

    # 4. 创建 benchmark_results 表
    op.create_table(
        'benchmark_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False, comment='所属评测运行ID'),
        sa.Column('case_id', sa.Integer(), nullable=False, comment='测试用例ID'),
        sa.Column('actual_skill_id', sa.String(200), nullable=True, comment='实际匹配的Skill ID'),
        sa.Column('actual_attributes', sa.JSON(), nullable=True, comment='实际输出属性'),
        sa.Column('actual_category', sa.JSON(), nullable=True, comment='实际类目'),
        sa.Column('actual_confidence', sa.Float(), nullable=True, comment='实际置信度'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='执行耗时(毫秒)'),
        sa.Column('skill_match', sa.Boolean(), nullable=True, comment='Skill是否匹配'),
        sa.Column('attribute_scores', sa.JSON(), nullable=True, 
                  comment='各属性评分 {"公称直径": {"match": true, "score": 1.0}, ...}'),
        sa.Column('overall_score', sa.Float(), nullable=True, comment='综合得分 0-1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending',
                  comment='状态: success/partial/failed/error'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['run_id'], ['benchmark_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['case_id'], ['benchmark_cases.id'], ondelete='CASCADE'),
        comment='Benchmark评测结果'
    )
    op.create_index('ix_benchmark_results_id', 'benchmark_results', ['id'])
    op.create_index('ix_benchmark_results_run_id', 'benchmark_results', ['run_id'])
    op.create_index('ix_benchmark_results_case_id', 'benchmark_results', ['case_id'])
    op.create_index('ix_benchmark_results_status', 'benchmark_results', ['status'])

    # 5. 创建 generation_templates 表
    op.create_table(
        'generation_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('template_code', sa.String(100), nullable=False, comment='模板编码'),
        sa.Column('template_name', sa.String(200), nullable=False, comment='模板名称'),
        sa.Column('domain', sa.String(100), nullable=True, comment='适用领域'),
        sa.Column('pattern', sa.Text(), nullable=False, 
                  comment='模板模式 "{材质}管 DN{公称直径} PN{公称压力}"'),
        sa.Column('variants', sa.JSON(), nullable=True, comment='变体列表'),
        sa.Column('noise_rules', sa.JSON(), nullable=True, 
                  comment='噪声规则 {"typo_rate": 0.1, "omit_unit": true}'),
        sa.Column('difficulty_weight', sa.String(50), nullable=True, comment='生成难度倾向'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='数据生成模板'
    )
    op.create_index('ix_generation_templates_id', 'generation_templates', ['id'])
    op.create_index('ix_generation_templates_code', 'generation_templates', ['template_code'], unique=True)
    op.create_index('ix_generation_templates_domain', 'generation_templates', ['domain'])


def downgrade() -> None:
    # 按创建的逆序删除
    op.drop_index('ix_generation_templates_domain', 'generation_templates')
    op.drop_index('ix_generation_templates_code', 'generation_templates')
    op.drop_index('ix_generation_templates_id', 'generation_templates')
    op.drop_table('generation_templates')

    op.drop_index('ix_benchmark_results_status', 'benchmark_results')
    op.drop_index('ix_benchmark_results_case_id', 'benchmark_results')
    op.drop_index('ix_benchmark_results_run_id', 'benchmark_results')
    op.drop_index('ix_benchmark_results_id', 'benchmark_results')
    op.drop_table('benchmark_results')

    op.drop_index('ix_benchmark_runs_status', 'benchmark_runs')
    op.drop_index('ix_benchmark_runs_dataset_id', 'benchmark_runs')
    op.drop_index('ix_benchmark_runs_code', 'benchmark_runs')
    op.drop_index('ix_benchmark_runs_id', 'benchmark_runs')
    op.drop_table('benchmark_runs')

    op.drop_index('ix_benchmark_cases_code', 'benchmark_cases')
    op.drop_index('ix_benchmark_cases_difficulty', 'benchmark_cases')
    op.drop_index('ix_benchmark_cases_dataset_id', 'benchmark_cases')
    op.drop_index('ix_benchmark_cases_id', 'benchmark_cases')
    op.drop_table('benchmark_cases')

    op.drop_index('ix_benchmark_datasets_status', 'benchmark_datasets')
    op.drop_index('ix_benchmark_datasets_code', 'benchmark_datasets')
    op.drop_index('ix_benchmark_datasets_id', 'benchmark_datasets')
    op.drop_table('benchmark_datasets')
