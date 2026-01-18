-- =====================================================
-- Migration: RBAC权限系统 + 校区SaaS化
-- Version: 001
-- Date: 2025-01-15
-- Description:
--   1. 新增权限相关表(resources, permissions, roles, role_permissions)
--   2. 修改现有表添加campus_id和role_id字段
--   3. 初始化系统数据
-- =====================================================

-- ==================== 1. 创建新表 ====================

-- 1.1 资源模块表
CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_time TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(150),
    updated_by VARCHAR(150)
);

COMMENT ON TABLE resources IS '系统资源模块表';
COMMENT ON COLUMN resources.code IS '资源编码(如dashboard, student, teacher等)';
COMMENT ON COLUMN resources.name IS '资源名称';

-- 1.2 权限定义表
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_time TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(150),
    updated_by VARCHAR(150),
    UNIQUE(resource_id, action)
);

COMMENT ON TABLE permissions IS '权限定义表';
COMMENT ON COLUMN permissions.action IS '操作类型: read/edit/delete';

-- 1.3 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_time TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(150),
    updated_by VARCHAR(150)
);

COMMENT ON TABLE roles IS '角色表';
COMMENT ON COLUMN roles.is_system IS '是否系统内置角色(不可删除)';

-- 1.4 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(150),
    UNIQUE(role_id, permission_id)
);

COMMENT ON TABLE role_permissions IS '角色权限关联表';

-- ==================== 2. 修改现有表 ====================

-- 2.1 users表添加role_id和campus_id
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INTEGER REFERENCES roles(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS campus_id INTEGER REFERENCES campuses(id);

COMMENT ON COLUMN users.role_id IS '关联角色ID';
COMMENT ON COLUMN users.campus_id IS '所属校区ID(超管为空表示无限制)';

-- 2.2 students表添加campus_id
ALTER TABLE students ADD COLUMN IF NOT EXISTS campus_id INTEGER REFERENCES campuses(id);
COMMENT ON COLUMN students.campus_id IS '所属校区ID';

-- 2.3 courses表添加campus_id
ALTER TABLE courses ADD COLUMN IF NOT EXISTS campus_id INTEGER REFERENCES campuses(id);
COMMENT ON COLUMN courses.campus_id IS '所属校区ID';

-- 2.4 schedules表添加campus_id和batch_no
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS campus_id INTEGER REFERENCES campuses(id);
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS batch_no VARCHAR(50);
COMMENT ON COLUMN schedules.campus_id IS '所属校区ID(冗余字段，从class_plan获取)';
COMMENT ON COLUMN schedules.batch_no IS '批量排课批次号(UUID)';

-- 2.5 enrollments表添加campus_id
ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS campus_id INTEGER REFERENCES campuses(id);
COMMENT ON COLUMN enrollments.campus_id IS '所属校区ID(冗余字段，从class_plan获取)';

-- ==================== 3. 创建索引 ====================

CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_campus_id ON users(campus_id);
CREATE INDEX IF NOT EXISTS idx_students_campus_id ON students(campus_id);
CREATE INDEX IF NOT EXISTS idx_courses_campus_id ON courses(campus_id);
CREATE INDEX IF NOT EXISTS idx_schedules_campus_id ON schedules(campus_id);
CREATE INDEX IF NOT EXISTS idx_schedules_batch_no ON schedules(batch_no);
CREATE INDEX IF NOT EXISTS idx_enrollments_campus_id ON enrollments(campus_id);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_id ON permissions(resource_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- ==================== 4. 初始化数据 ====================

-- 4.1 插入资源模块
INSERT INTO resources (code, name, description, sort_order, is_active, created_by) VALUES
    ('dashboard', '仪表盘', '首页仪表盘', 0, true, 'system'),
    ('student', '学生管理', '学生信息管理', 1, true, 'system'),
    ('teacher', '教师管理', '教师信息管理', 2, true, 'system'),
    ('course', '课程管理', '课程产品管理', 3, true, 'system'),
    ('class_plan', '开班管理', '班级计划管理', 4, true, 'system'),
    ('enrollment', '报名管理', '学生报名管理', 5, true, 'system'),
    ('schedule', '排课管理', '课表排课管理', 6, true, 'system'),
    ('campus', '校区管理', '校区信息管理', 7, true, 'system'),
    ('classroom', '教室管理', '教室信息管理', 8, true, 'system'),
    ('user', '用户管理', '系统用户管理', 9, true, 'system'),
    ('dictionary', '数据字典', '系统数据字典', 10, true, 'system'),
    ('role_permission', '角色权限', '角色权限配置', 11, true, 'system'),
    ('system', '系统管理', '系统设置', 12, true, 'system')
ON CONFLICT (code) DO NOTHING;

-- 4.2 为每个资源创建read/edit/delete权限
INSERT INTO permissions (resource_id, action, name, created_by)
SELECT r.id, a.action, r.name || '-' ||
    CASE a.action
        WHEN 'read' THEN '查看'
        WHEN 'edit' THEN '编辑'
        WHEN 'delete' THEN '删除'
    END,
    'system'
FROM resources r
CROSS JOIN (VALUES ('read'), ('edit'), ('delete')) AS a(action)
ON CONFLICT (resource_id, action) DO NOTHING;

-- 4.3 插入系统角色
INSERT INTO roles (code, name, description, is_system, is_active, created_by) VALUES
    ('super_admin', '超级管理员', '拥有所有权限，不受校区限制', true, true, 'system'),
    ('campus_admin', '校区管理员', '管理所属校区的业务数据', true, true, 'system'),
    ('teacher', '教师', '查看课表和学生信息', true, true, 'system'),
    ('student', '学生', '查看自己的课表和报名信息', true, true, 'system')
ON CONFLICT (code) DO NOTHING;

-- 4.4 为超级管理员分配所有权限
INSERT INTO role_permissions (role_id, permission_id, created_by)
SELECT r.id, p.id, 'system'
FROM roles r
CROSS JOIN permissions p
WHERE r.code = 'super_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 4.5 为校区管理员分配业务权限
INSERT INTO role_permissions (role_id, permission_id, created_by)
SELECT r.id, p.id, 'system'
FROM roles r
JOIN permissions p ON true
JOIN resources res ON p.resource_id = res.id
WHERE r.code = 'campus_admin'
  AND res.code IN ('dashboard', 'student', 'teacher', 'course', 'class_plan', 'enrollment', 'schedule', 'campus', 'classroom')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 4.6 为教师分配只读权限
INSERT INTO role_permissions (role_id, permission_id, created_by)
SELECT r.id, p.id, 'system'
FROM roles r
JOIN permissions p ON p.action = 'read'
JOIN resources res ON p.resource_id = res.id
WHERE r.code = 'teacher'
  AND res.code IN ('dashboard', 'student', 'class_plan', 'enrollment', 'schedule')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 4.7 为学生分配最少权限
INSERT INTO role_permissions (role_id, permission_id, created_by)
SELECT r.id, p.id, 'system'
FROM roles r
JOIN permissions p ON p.action = 'read'
JOIN resources res ON p.resource_id = res.id
WHERE r.code = 'student'
  AND res.code IN ('dashboard', 'schedule')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ==================== 5. 数据迁移 ====================

-- 5.1 将现有admin用户关联到super_admin角色
UPDATE users
SET role_id = (SELECT id FROM roles WHERE code = 'super_admin')
WHERE role = 'admin' AND role_id IS NULL;

-- 5.2 将现有teacher用户关联到teacher角色
UPDATE users
SET role_id = (SELECT id FROM roles WHERE code = 'teacher')
WHERE role = 'teacher' AND role_id IS NULL;

-- 5.3 将现有student用户关联到student角色
UPDATE users
SET role_id = (SELECT id FROM roles WHERE code = 'student')
WHERE role = 'student' AND role_id IS NULL;

-- 5.4 为现有学生设置默认校区(如果有班级关联)
UPDATE students s
SET campus_id = (
    SELECT DISTINCT cp.campus_id
    FROM enrollments e
    JOIN class_plans cp ON e.class_plan_id = cp.id
    WHERE e.student_id = s.id
    LIMIT 1
)
WHERE s.campus_id IS NULL;

-- 5.5 为现有课程设置默认校区(从关联的班级获取)
UPDATE courses c
SET campus_id = (
    SELECT DISTINCT cp.campus_id
    FROM class_plans cp
    WHERE cp.course_id = c.id
    LIMIT 1
)
WHERE c.campus_id IS NULL;

-- 5.6 为现有排课设置campus_id(从班级获取)
UPDATE schedules s
SET campus_id = (
    SELECT cp.campus_id
    FROM class_plans cp
    WHERE cp.id = s.class_plan_id
)
WHERE s.campus_id IS NULL;

-- 5.7 为现有报名设置campus_id(从班级获取)
UPDATE enrollments e
SET campus_id = (
    SELECT cp.campus_id
    FROM class_plans cp
    WHERE cp.id = e.class_plan_id
)
WHERE e.campus_id IS NULL;

-- ==================== 完成 ====================
SELECT 'Migration 001 completed successfully!' AS status;
