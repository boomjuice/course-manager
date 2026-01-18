-- 迁移脚本: 003_student_status_update.sql
-- 说明: 更新学生状态值为新定义的状态体系

-- 执行时间: 2026-01-17

-- =============================================================================
-- 学生状态更新说明
-- =============================================================================
-- 旧状态值 -> 新状态值映射:
-- active (在读) -> enrolled (已报名)
-- suspended (暂停) -> enrolled (已报名) - 视为已报名但暂时暂停
-- graduated (结业) -> graduated (已结业) - 保持不变
-- dropped (退学) -> unenrolled (未报名) - 视为未报名
--
-- 注意: 这个迁移假设没有"studying"(上课中)状态的学生数据
-- 如果需要严格区分"已报名"和"上课中"，需要额外业务逻辑

-- =============================================================================
-- 执行状态更新
-- =============================================================================

-- 更新状态为 'active' -> 'enrolled'
UPDATE students SET status = 'enrolled' WHERE status = 'active';

-- 更新状态为 'suspended' -> 'enrolled'
UPDATE students SET status = 'enrolled' WHERE status = 'suspended';

-- 更新状态为 'dropped' -> 'unenrolled'
UPDATE students SET status = 'unenrolled' WHERE status = 'dropped';

-- 'graduated' 保持不变

-- =============================================================================
-- 可选：更新字典数据（如果字典表中也有学生状态）
-- =============================================================================
-- 如果有字典表，需要更新对应的字典值
-- INSERT INTO dictionaries (name, code, value, label, sort_order, is_system)
-- VALUES ('student_status', 'student_status', 'unenrolled', '未报名', 1, true);
-- INSERT INTO dictionaries (name, code, value, label, sort_order, is_system)
-- VALUES ('student_status', 'student_status', 'enrolled', '已报名', 2, true);
-- INSERT INTO dictionaries (name, code, value, label, sort_order, is_system)
-- VALUES ('student_status', 'student_status', 'studying', '上课中', 3, true);
-- INSERT INTO dictionaries (name, code, value, label, sort_order, is_system)
-- VALUES ('student_status', 'student_status', 'graduated', '已结业', 4, true);

-- =============================================================================
-- 验证更新结果
-- =============================================================================
-- SELECT status, COUNT(*) as count FROM students GROUP BY status ORDER BY status;
