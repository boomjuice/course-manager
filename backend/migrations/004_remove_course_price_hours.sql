-- 迁移脚本: 004_remove_course_price_hours.sql
-- 说明: 从课程产品移除价格(price)和总课时(total_hours)字段

-- 执行时间: 2026-01-17

-- =============================================================================
-- 从 courses 表移除 price 和 total_hours 字段
-- =============================================================================

-- 注意: 如果表中有数据，转换可能会失败

-- 方式1: 直接删除列
ALTER TABLE courses DROP COLUMN IF EXISTS price;
ALTER TABLE courses DROP COLUMN IF EXISTS total_hours;

-- =============================================================================
-- 验证修改
-- =============================================================================
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'courses' AND column_name IN ('price', 'total_hours');
-- 应该返回空结果
