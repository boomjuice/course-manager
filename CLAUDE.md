# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

课程管理系统 v2.0 - 现代化教育培训管理平台。前后端分离架构，支持多校区、RBAC权限控制、角色化仪表盘。

## 技术栈

**后端 (backend/)**
- FastAPI + SQLAlchemy 2.0 (async)
- PostgreSQL + asyncpg
- JWT认证 (python-jose)
- APScheduler 定时任务

**前端 (frontend/)**
- Vue 3 + TypeScript + Vite
- Element Plus UI
- Pinia 状态管理
- Vue Router
- ECharts 数据可视化

## 开发命令

### 后端
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器 (端口8000)
python -m app.main
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试 (使用内存SQLite)
pytest

# 运行单个测试文件
pytest tests/test_rbac.py -v

# 运行特定测试
pytest tests/test_rbac.py::test_function_name -v

# 代码格式化
black .
isort .

# 类型检查
mypy .

# 初始化管理员 (首次部署)
cd scripts && python init_admin.py

# 初始化字典数据
cd scripts && python init_dict.py
```

### 前端
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (端口5173)
npm run dev

# 构建生产版本
npm run build

# 类型检查
vue-tsc -b
```

## 核心架构

### 后端分层结构
```
backend/app/
├── main.py              # FastAPI入口，lifespan管理
├── config.py            # Pydantic Settings配置
├── database.py          # SQLAlchemy async引擎和会话
├── api/
│   ├── deps.py          # 核心依赖注入(认证、RBAC权限、校区过滤)
│   └── v1/
│       ├── dashboard.py # 角色化仪表盘API（学生/教师/管理员）
│       └── ...          # 其他API路由模块
├── models/              # SQLAlchemy ORM模型
├── schemas/
│   ├── dashboard.py     # 仪表盘相关Schema定义
│   └── ...              # 其他Pydantic模型
├── services/            # 业务逻辑层
└── core/
    ├── security.py      # JWT令牌、密码哈希
    ├── exceptions.py    # 自定义异常
    └── scheduler.py     # APScheduler定时任务
```

### 权限系统 (RBAC)

核心实现在 `api/deps.py`：

- **PermissionChecker**: 检查 `resource:action` 格式权限
- **CampusScopedQuery**: JWT中提取campus_id进行数据隔离
- 快捷类型别名: `StudentRead`, `TeacherEdit`, `ScheduleDelete` 等

```python
# 使用示例
@router.get("/students")
async def list_students(user: StudentRead):  # 自动检查 student:read 权限
    ...
```

### 统一响应格式

所有API返回 `ResponseModel`:
```json
{
  "code": 0,
  "message": "success",
  "data": {...},
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 前端权限控制

- 路由守卫: `router/index.ts` 中检查 `meta.permission`
- 权限指令: `v-permission="['student', 'edit']"` 控制按钮显示
- 权限Store: `stores/permission.ts` 管理用户权限

### 角色化仪表盘系统

根据用户角色展示不同的仪表盘视图：

**后端 API (`api/v1/dashboard.py`):**
- `GET /dashboard/student` - 学生仪表盘（课程进度、出勤统计）
- `GET /dashboard/teacher` - 教师仪表盘（课程安排、学生出勤）
- `GET /dashboard/admin/overview` - 管理员概览（校区统计、KPI指标）
- `GET /dashboard/admin/students` - 学生分析（分布、趋势）
- `GET /dashboard/admin/teachers` - 教师分析（工作量、绩效）
- `GET /dashboard/admin/classes` - 课程分析（开班情况、满班率）

**前端组件 (`views/Dashboard/`):**
```
Dashboard/
├── DashboardView.vue           # 仪表盘入口（角色路由）
├── AdminDashboard.vue          # 管理员仪表盘主视图
└── components/
    ├── KpiCard.vue             # KPI指标卡片
    ├── TrendChart.vue          # 趋势图表（ECharts）
    ├── DistributionChart.vue   # 分布图表（饼图/柱状图）
    └── TimeRangeSelector.vue   # 时间范围选择器
```

## 数据模型关系

- **Campus** → Classroom, Course, Student, ClassPlan (校区隔离)
- **Teacher** → 无校区限制，可跨校区授课
- **User** → UserRole → RolePermission → Permission → Resource
- **ClassPlan** → Course, Teacher, Classroom, Schedule, Enrollment

## 测试

测试使用内存SQLite，自动patch ARRAY类型为JSON。主要fixtures在 `tests/conftest.py`：

- `test_users`: 含super_admin、campus_admin、teacher、student
- `test_campuses`: 北京/上海两个校区
- `super_admin_token`、`bj_admin_token`: 预生成JWT令牌

**测试文件:**
```bash
# RBAC和权限测试
pytest tests/test_rbac.py -v
pytest tests/test_permission.py -v

# 校区隔离测试
pytest tests/test_campus_isolation.py -v

# 仪表盘测试（学生/教师/管理员）
pytest tests/test_dashboard_student.py -v
pytest tests/test_dashboard_teacher.py -v
pytest tests/test_dashboard_admin.py -v
```

## 环境配置

复制 `backend/.env.example` 为 `.env`，必须配置：
- `DATABASE_URL`: PostgreSQL连接串
- `SECRET_KEY`: JWT密钥（生产环境必须修改）

默认账号: admin / admin123

## API文档

开发模式下访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
