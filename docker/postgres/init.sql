-- 初始化数据库
-- 创建 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Milestone 2: Pages 和 Candidates 表
CREATE TABLE IF NOT EXISTS pages (
    id VARCHAR(64) PRIMARY KEY,
    image_url TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR(64) PRIMARY KEY,
    page_id VARCHAR(64) NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    confidence REAL NOT NULL,
    quad JSONB NOT NULL,  -- [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    bbox JSONB NOT NULL,  -- {"x": 120, "y": 80, "w": 420, "h": 64}
    angle_deg REAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_page_id ON candidates(page_id);

-- Milestone 3: Patches 表
CREATE TABLE IF NOT EXISTS patches (
    id VARCHAR(64) PRIMARY KEY,
    page_id VARCHAR(64) NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    candidate_id VARCHAR(64) REFERENCES candidates(id) ON DELETE SET NULL,
    bbox JSONB NOT NULL,  -- {"x": 110, "y": 72, "w": 440, "h": 84}
    image_url TEXT NOT NULL,
    debug_info JSONB,  -- {"bg_model": "solid", "mae": 6.1, ...}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patches_page_id ON patches(page_id);
CREATE INDEX IF NOT EXISTS idx_patches_candidate_id ON patches(candidate_id);

-- 打印初始化信息
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL database initialized successfully';
    RAISE NOTICE 'Milestone 3: Pages, Candidates, and Patches tables created';
END $$;
