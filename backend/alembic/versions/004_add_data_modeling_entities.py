"""Add data modeling entities: StandardSeries, Domain, Category, SkillFamily, AttributeDefinition

Revision ID: 004_add_data_modeling
Revises: 003_add_llm_usage_logs
Create Date: 2026-02-13

This migration adds the following tables:
- domains: 动态推断的领域实体
- standard_series: 标准系列聚合实体
- categories: 4级类目树
- skill_families: 技能族
- skill_family_members: 技能族成员关联
- attribute_definitions: 属性定义
- domain_attributes: 领域-属性关联

And modifies:
- standards: 添加 series_id, domain_id, category_id, part_number
- skills: 添加 domain_id, category_id
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建 domains 表 (需要先创建，因为其他表依赖它)
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('domain_code', sa.String(50), nullable=False),
        sa.Column('domain_name', sa.String(200), nullable=False),
        sa.Column('color', sa.String(20), nullable=False),
        sa.Column('sector_angle', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('standard_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_domains_id', 'domains', ['id'])
    op.create_index('ix_domains_domain_code', 'domains', ['domain_code'], unique=True)

    # 2. 创建 standard_series 表
    op.create_table(
        'standard_series',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('series_code', sa.String(100), nullable=False),
        sa.Column('series_name', sa.String(500), nullable=True),
        sa.Column('domain_id', sa.Integer(), sa.ForeignKey('domains.id'), nullable=True),
        sa.Column('part_count', sa.Integer(), server_default='1', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_standard_series_id', 'standard_series', ['id'])
    op.create_index('ix_standard_series_series_code', 'standard_series', ['series_code'], unique=True)

    # 3. 创建 categories 表 (自引用，需要特殊处理)
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category_code', sa.String(100), nullable=False),
        sa.Column('category_name', sa.String(200), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('domain_id', sa.Integer(), sa.ForeignKey('domains.id'), nullable=True),
        sa.Column('full_path', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('standard_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('skill_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], name='fk_categories_parent_id')
    )
    op.create_index('ix_categories_id', 'categories', ['id'])
    op.create_index('ix_categories_category_code', 'categories', ['category_code'], unique=True)
    op.create_index('ix_categories_level', 'categories', ['level'])

    # 4. 创建 skill_families 表
    op.create_table(
        'skill_families',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('family_code', sa.String(100), nullable=False),
        sa.Column('family_name', sa.String(500), nullable=False),
        sa.Column('series_id', sa.Integer(), sa.ForeignKey('standard_series.id'), nullable=True),
        sa.Column('domain_id', sa.Integer(), sa.ForeignKey('domains.id'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('skill_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skill_families_id', 'skill_families', ['id'])
    op.create_index('ix_skill_families_family_code', 'skill_families', ['family_code'], unique=True)

    # 5. 创建 attribute_definitions 表
    op.create_table(
        'attribute_definitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('attribute_code', sa.String(100), nullable=False),
        sa.Column('attribute_name', sa.String(200), nullable=False),
        sa.Column('attribute_name_en', sa.String(200), nullable=True),
        sa.Column('data_type', sa.String(50), server_default='string', nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('patterns', sa.JSON(), nullable=True),
        sa.Column('synonyms', sa.JSON(), nullable=True),
        sa.Column('validation_rules', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_common', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attribute_definitions_id', 'attribute_definitions', ['id'])
    op.create_index('ix_attribute_definitions_attribute_code', 'attribute_definitions', ['attribute_code'], unique=True)

    # 6. 创建 domain_attributes 关联表
    op.create_table(
        'domain_attributes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('domain_id', sa.Integer(), sa.ForeignKey('domains.id'), nullable=False),
        sa.Column('attribute_id', sa.Integer(), sa.ForeignKey('attribute_definitions.id'), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('default_value', sa.String(500), nullable=True),
        sa.Column('domain_specific_rules', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_domain_attributes_id', 'domain_attributes', ['id'])

    # 7. 创建 skill_family_members 关联表
    op.create_table(
        'skill_family_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('family_id', sa.Integer(), sa.ForeignKey('skill_families.id'), nullable=False),
        sa.Column('skill_id', sa.Integer(), sa.ForeignKey('skills.id'), nullable=False),
        sa.Column('role', sa.String(50), server_default='member', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skill_family_members_id', 'skill_family_members', ['id'])

    # 8. 修改 standards 表，添加新字段（先添加列，不带外键）
    op.add_column('standards', sa.Column('series_id', sa.Integer(), nullable=True))
    op.add_column('standards', sa.Column('domain_id', sa.Integer(), nullable=True))
    op.add_column('standards', sa.Column('category_id', sa.Integer(), nullable=True))
    op.add_column('standards', sa.Column('part_number', sa.Integer(), nullable=True))

    # 9. 修改 skills 表，添加新字段（先添加列，不带外键）
    op.add_column('skills', sa.Column('domain_id', sa.Integer(), nullable=True))
    op.add_column('skills', sa.Column('category_id', sa.Integer(), nullable=True))

    # 10. 添加外键约束（分离出来，确保被引用表已存在）
    op.create_foreign_key('fk_standard_series', 'standards', 'standard_series', ['series_id'], ['id'])
    op.create_foreign_key('fk_standard_domain', 'standards', 'domains', ['domain_id'], ['id'])
    op.create_foreign_key('fk_standard_category', 'standards', 'categories', ['category_id'], ['id'])
    op.create_foreign_key('fk_skill_domain', 'skills', 'domains', ['domain_id'], ['id'])
    op.create_foreign_key('fk_skill_category', 'skills', 'categories', ['category_id'], ['id'])


def downgrade() -> None:
    # 1. 先删除外键约束
    op.drop_constraint('fk_skill_category', 'skills', type_='foreignkey')
    op.drop_constraint('fk_skill_domain', 'skills', type_='foreignkey')
    op.drop_constraint('fk_standard_category', 'standards', type_='foreignkey')
    op.drop_constraint('fk_standard_domain', 'standards', type_='foreignkey')
    op.drop_constraint('fk_standard_series', 'standards', type_='foreignkey')

    # 2. 移除 skills 表的新字段
    op.drop_column('skills', 'category_id')
    op.drop_column('skills', 'domain_id')

    # 3. 移除 standards 表的新字段
    op.drop_column('standards', 'part_number')
    op.drop_column('standards', 'category_id')
    op.drop_column('standards', 'domain_id')
    op.drop_column('standards', 'series_id')

    # 删除关联表
    op.drop_index('ix_skill_family_members_id', 'skill_family_members')
    op.drop_table('skill_family_members')

    op.drop_index('ix_domain_attributes_id', 'domain_attributes')
    op.drop_table('domain_attributes')

    # 删除主要表 (按依赖顺序逆序删除)
    op.drop_index('ix_attribute_definitions_attribute_code', 'attribute_definitions')
    op.drop_index('ix_attribute_definitions_id', 'attribute_definitions')
    op.drop_table('attribute_definitions')

    op.drop_index('ix_skill_families_family_code', 'skill_families')
    op.drop_index('ix_skill_families_id', 'skill_families')
    op.drop_table('skill_families')

    op.drop_index('ix_categories_level', 'categories')
    op.drop_index('ix_categories_category_code', 'categories')
    op.drop_index('ix_categories_id', 'categories')
    op.drop_table('categories')

    op.drop_index('ix_standard_series_series_code', 'standard_series')
    op.drop_index('ix_standard_series_id', 'standard_series')
    op.drop_table('standard_series')

    op.drop_index('ix_domains_domain_code', 'domains')
    op.drop_index('ix_domains_id', 'domains')
    op.drop_table('domains')
