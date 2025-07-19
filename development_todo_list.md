# 排课系统开发任务清单 (Development TODO List)

---

## 后端开发 (Backend)

### 阶段一：项目初始化与基础配置

- [x] **D.1.1: 初始化 Django 项目**
  - [x] `django-admin startproject course_manager .`
  - [x] 创建一个新的 app, 例如: `python manage.py startapp api`

- [x] **D.1.2: 配置环境变量**
  - [x] 创建 `.env` 文件用于存储敏感信息 (e.g., `SECRET_KEY`, `DATABASE_URL`).
  - [x] 在 `settings.py` 中使用 `python-decouple` 或 `django-environ` 加载配置.

- [x] **D.1.3: 配置数据库**
  - [x] 在 `settings.py` 中配置 PostgreSQL 数据库连接.
  - [x] 安装 `psycopg2-binary`.

- [x] **D.1.4: 安装并配置 Django REST Framework (DRF)**
  - [x] `pip install djangorestframework`
  - [x] 将 `'rest_framework'` 和 `'rest_framework.authtoken'` 添加到 `INSTALLED_APPS`.
  - [x] 在 `settings.py` 中设置默认的认证、权限和分页类。

- [x] **D.1.5: 配置日志 (Logging)**
  - [x] 在 `settings.py` 中设置 `LOGGING`，将日志输出到文件和控制台。

- [x] **D.1.6: 配置跨域 (CORS)**
  - [x] `pip install django-cors-headers`
  - [x] 在 `settings.py` 中配置 `CORS_ALLOWED_ORIGINS` 和中间件。

### 阶段二：数据库模型与迁移

- [x] **D.2.1: 实现基础模型**
  - [x] 在 `api/models.py` 中创建 `Campus`, `Subject`, `Grade`, `Tag`, `Classroom`, `TimeSlot` 模型.

- [x] **D.2.2: 实现核心业务模型**
  - [x] 创建 `Teacher`, `Student`, `TeachingClass`, `ScheduleEntry` 模型.

- [x] **D.2.3: 生成和执行数据库迁移**
  - [x] `python manage.py makemigrations`
  - [x] `python manage.py migrate`

### 阶段三：核心 API 开发

- [x] **D.3.1: 用户认证 API**
  - [x] 实现登录接口 `POST /api/auth/login/`.

- [x] **D.3.2: 基础信息管理 (CRUD) API**
  - [x] 为 `Campus`, `Classroom`, `Subject`, `Grade`, `Tag` 创建 Serializer 和 ViewSet.
  - [x] 为 `Teacher` 和 `Student` 创建 Serializer 和 ViewSet.
  - [x] 为 `TeachingClass` 创建 Serializer 和 ViewSet.
  - [x] **性能优化**: 在所有列表视图中使用 `select_related` 和 `prefetch_related`.
  - [x] **权限控制**: 为每个 ViewSet 设置合适的权限.

- [x] **D.3.3: 课表核心功能 API**
  - [x] **查询课表**: 创建 `ScheduleEntry` 的 Serializer 和 List/Retrieve View (支持筛选).
  - [x] **创建/修改课表条目**: 实现冲突检测逻辑 (教师、教室、学生).
  - [x] **批量创建课表**: 实现 `POST /api/schedule/batch-create/` 接口 (使用事务).

- [x] **D.3.4: 辅助功能 API**
  - [x] **智能分组推荐**: 创建 `GET /api/students/recommendations/` 接口.

### 阶段四：后端测试

- [x] **D.4.1: 编写单元测试**
  - [x] 为冲突检测逻辑编写单元测试.
- [x] **D.4.2: 编写集成测试**
  - [x] 为认证、批量创建、查询筛选等关键 API 编写集成测试.

---

## 前端开发 (Frontend - Vue.js)

### 阶段五：项目初始化与基础配置

- [x] **F.5.1: 初始化 Vue 项目**
  - [x] 使用 Vue CLI 或 Vite 创建项目: `npm create vue@latest`.
  - [x] 选择 `Vue Router` 和 `Pinia` (或 `Vuex`) 进行状态管理.

- [x] **F.5.2: UI 框架集成**
  - [x] 选择并集成一个 UI 框架 (例如: `Element Plus`, `Ant Design Vue`).

- [x] **F.5.3: API 请求封装**
  - [x] 安装 `axios`.
  - [x] 封装 `axios` 实例，统一处理请求头 (Authorization Token)、基础 URL 和响应拦截器 (处理401等).

- [x] **F.5.4: 设置路由 (Vue Router)**
  - [x] 创建路由表，配置登录页、布局页 (Layout) 和各个功能页面的路由。
  - [x] 配置路由守卫 (Navigation Guards)，实现未登录用户跳转到登录页的逻辑。

### 阶段六：核心页面开发

- [x] **F.6.1: 登录页面**
  - [x] 创建登录表单 (用户名、密码).
  - [x] 调用登录 API，成功后将 Token 存入 `localStorage` 或 `sessionStorage`，并跳转到主页。
  - [x] 使用 Pinia/Vuex 管理用户登录状态和 Token。

- [x] **F.6.2: 主布局 (Layout)**
  - [x] 创建包含侧边栏导航、顶部用户信息和主内容区域的布局组件。

- [x] **F.6.3: 基础信息管理页面**
  - [x] 创建教师管理、学生管理、课程管理、教室管理等页面的组件。
  - [x] 每个页面实现数据的增、删、改、查功能，并与后端 API 对接。
  - [x] 使用表格组件展示数据，并包含分页功能。
  - [x] 使用模态框 (Modal/Dialog) 或独立页面来处理创建和编辑操作。

- [x] **F.6.4: 核心课表页面**
  - [x] **日历/表格视图**: 选择一个日历组件 (如 `FullCalendar` 或 `Element Plus Calendar`) 或自建表格来展示课表。
  - [x] **数据获取与展示**: 调用 `GET /api/schedule/entries/` 接口，将课程数据显示在视图上。
  - [x] **筛选功能**: 提供按教师、学生、教室筛选课表的 UI 控件，并调用 API 刷新视图。
  - [ ] **拖拽调整 (可选)**: 实现课程在日历上的拖拽功能，拖拽结束后调用 API 更新课程时间。

- [ ] **F.6.5: 管理员统计视图**
  - [ ] 设计并实现一个仪表盘 (Dashboard) 页面。
  - [ ] 使用图表库 (如 `ECharts`, `Chart.js`) 展示关键指标，例如：教师课时统计、教室利用率等。

### 阶段七：联调与测试

- [x] **F.7.1: 前后端接口联调**
  - [x] 确保所有前端页面都能正确地从后端获取数据并提交数据。
  - [x] 调用并解决跨域 (CORS) 问题。
  - [x] 统一处理 API 错误，并向用户提供清晰的提示。

- [ ] **F.7.2: 前端组件测试 (可选)**
  - [ ] 使用 `Vitest` 或 `Jest` 为关键组件 (如课表日历) 编写单元测试。