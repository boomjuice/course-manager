-- Migration: Add equipment column to classrooms table
-- Description: 添加教室设备配置字段（JSON格式存储key-value）
-- Date: 2025-01-18

-- Add equipment column (JSON type for key-value storage)
ALTER TABLE classrooms
ADD COLUMN IF NOT EXISTS equipment JSONB DEFAULT NULL;

-- Comment on column
COMMENT ON COLUMN classrooms.equipment IS '设备配置（key-value形式）';

-- Optional: Migrate existing description data to equipment (if needed)
-- UPDATE classrooms
-- SET equipment = jsonb_build_object('设备', description)
-- WHERE description IS NOT NULL AND description != '';
