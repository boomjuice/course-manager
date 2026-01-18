-- 迁移脚本: 002_decimal_hours_support.sql
-- 说明: 支持小数课时数，将课时数字段改为numeric(6,1)

-- 执行时间: 2026-01-17

-- =============================================================================
-- 修改 schedules 表的 lesson_hours 字段
-- =============================================================================
-- 注意: 如果表中有数据，转换可能会失败，需要先处理现有数据

-- 方式1: 如果字段当前是 integer，直接修改类型
ALTER TABLE schedules ALTER COLUMN lesson_hours TYPE numeric(6,1);

-- 如果上面的语句报错（可能因为有约束或依赖），可以先用临时字段中转:
-- 1. 添加临时字段
-- ALTER TABLE schedules ADD COLUMN lesson_hours_temp numeric(6,1);
-- 2. 复制数据
-- UPDATE schedules SET lesson_hours_temp = lesson_hours::numeric(6,1);
-- 3. 删除旧字段
-- ALTER TABLE schedules DROP COLUMN lesson_hours CASCADE;
-- 4. 重命名新字段
-- ALTER TABLE schedules RENAME COLUMN lesson_hours_temp TO lesson_hours;

-- =============================================================================
-- 修改 class_plans 表的 total_lessons 字段
-- =============================================================================
ALTER TABLE class_plans ALTER COLUMN total_lessons TYPE numeric(6,1);

-- =============================================================================
-- 验证修改
-- =============================================================================
-- SELECT column_name, data_type, numeric_precision, numeric_scale
-- FROM information_schema.columns
-- WHERE table_name = 'schedules' AND column_name = 'lesson_hours';

-- SELECT column_name, data_type, numeric_precision, numeric_scale
-- FROM information_schema.columns
-- WHERE table_name = 'class_plans' AND column_name = 'total_lessons';
