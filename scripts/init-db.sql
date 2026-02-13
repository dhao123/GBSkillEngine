-- GBSkillEngine 数据库初始化脚本
-- 此脚本在 PostgreSQL 容器首次启动时自动执行

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建索引用于全文搜索优化
-- 注意：实际表结构由 Alembic 迁移创建，这里只创建扩展和基础配置

-- 设置默认时区
SET timezone = 'Asia/Shanghai';

-- 创建只读用户 (可选，用于报表等只读场景)
-- DO $$
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gbskill_readonly') THEN
--         CREATE ROLE gbskill_readonly WITH LOGIN PASSWORD 'readonly_password';
--     END IF;
-- END
-- $$;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE 'GBSkillEngine 数据库初始化完成';
END
$$;
