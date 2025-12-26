-- 初始化数据库
-- Milestone 1: 仅创建基础扩展,表结构后续添加

-- 创建 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 打印初始化信息
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL database initialized successfully';
    RAISE NOTICE 'Milestone 1: Basic extensions created';
    RAISE NOTICE 'Table structures will be added in Milestone 2';
END $$;
