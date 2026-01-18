# 数据库迁移脚本

## 迁移列表

| 版本 | 文件 | 说明 |
|------|------|------|
| 001 | `001_rbac_and_campus_isolation.sql` | RBAC权限系统 + 校区SaaS化 |
| 002 | `002_decimal_hours_support.sql` | 支持小数课时数 |
| 003 | `003_student_status_update.sql` | 学生状态更新为新体系 |
| 004 | `004_remove_course_price_hours.sql` | 课程产品移除价格和课时字段 |

## 执行方法

### 方法1: 使用psql命令行

```bash
# 连接数据库执行迁移
psql -h localhost -U postgres -d course_manager_v2 -f migrations/001_rbac_and_campus_isolation.sql
```

### 方法2: 使用Python脚本

```bash
cd backend
python -c "
import asyncio
from app.database import engine
from sqlalchemy import text

async def run_migration():
    with open('migrations/001_rbac_and_campus_isolation.sql', 'r') as f:
        sql = f.read()
    async with engine.begin() as conn:
        # 逐条执行SQL（用分号分割）
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                await conn.execute(text(statement))
    print('Migration completed!')

asyncio.run(run_migration())
"
```

### 方法3: 在数据库管理工具中执行

1. 打开 DBeaver / pgAdmin / Navicat 等工具
2. 连接到 `course_manager_v2` 数据库
3. 打开 `001_rbac_and_campus_isolation.sql` 文件
4. 执行全部SQL

## 迁移内容说明

### 001_rbac_and_campus_isolation.sql

**新增表:**
- `resources` - 系统资源模块表
- `permissions` - 权限定义表
- `roles` - 角色表
- `role_permissions` - 角色权限关联表

**修改表:**
- `users` - 添加 `role_id`, `campus_id`
- `students` - 添加 `campus_id`
- `courses` - 添加 `campus_id`
- `schedules` - 添加 `campus_id`, `batch_no`
- `enrollments` - 添加 `campus_id`

**初始化数据:**
- 13个系统资源模块
- 39个权限（每个资源3个：read/edit/delete）
- 4个系统角色（super_admin/campus_admin/teacher/student）
- 角色权限配置

**数据迁移:**
- 现有用户自动关联到对应角色
- 现有学生/课程/排课/报名自动关联校区
