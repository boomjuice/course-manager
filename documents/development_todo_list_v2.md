# 排课系统V2开发任务清单 (Development TODO List V2.1)

---

## 后端开发 (Backend)

### 阶段一：项目升级与基础配置 (Project Upgrade & Configuration)

- [x] **D.1.1: 集成 Celery 和 Redis**
  - [x] `pip install celery redis`
  - [x] 在 `settings.py` 中配置 Celery Broker (Redis).
  - [x] 创建 `celery.py` 配置文件.

- [x] **D.1.2: 创建通用基类 `BaseModel`**
  - [x] 在 `api/models.py` (或独立的 `core/models.py`) 中创建 `BaseModel` 抽象模型.
  - [x] `BaseModel` 包含 `created_time`, `updated_time`, `created_by`, `updated_by` 字段.
  - [ ] 实现自动填充 `created_by` 和 `updated_by` 的逻辑 (例如通过中间件或重写 `save` 方法).

### 阶段二：数据库模型重构 (Database Model Refactoring)

- [x] **D.2.1: 实现数据字典模型**
  - [x] 创建 `DataDictionary` 模型，用于管理年级、科目、课程类型等.
  - [x] 编写数据迁移脚本，将旧的 `Subject`, `Grade`, `Tag` 数据迁移到 `DataDictionary`.

- [x] **D.2.2: 实现核心业务模型**
  - [x] 创建 `CourseProduct` 模型.
  - [x] 创建 `Enrollment` 模型.
  - [x] 创建 `StudyGroup` 模型.
  - [x] 创建 `Attendance` 模型.

- [x] **D.2.3: 重构现有模型**
  - [x] 修改 `Teacher`, `Student`, `Classroom`, `Campus` 模型，使其继承自 `BaseModel`.
  - [x] **核心**: 重构 `ScheduleEntry` 模型，使其成为历史快照，增加冗余字段 (`teacher_name`, `classroom_name`, etc.)，并关联到 `Enrollment`.
  - [x] 移除旧的 `TeachingClass` 和 `TimeSlot` 模型.

- [x] **D.2.4: 生成和执行数据库迁移**
  - [x] `python manage.py makemigrations`
  - [x] `python manage.py migrate`
  - [x] 验证数据迁移是否成功.

### 阶段三：核心 API 重构 (Core API Refactoring)

- [x] **D.3.1: 基础数据 API**
  - [x] 创建 `DataDictionary` 的 ViewSet (应支持按 `group_code` 筛选).
  - [x] 创建 `CourseProduct` 的 ViewSet (CRUD).

- [x] **D.3.2: 核心业务 API**
  - [x] 创建 `Enrollment` 的 ViewSet (CRUD).
  - [x] 创建 `StudyGroup` 的 ViewSet (CRUD), 包括添加/移除 `enrollments`.
  - [x] 创建 `Attendance` 的 ViewSet (CRUD).

- [x] **D.3.3: 重构课表 API**
  - [x] 重构 `POST /api/schedule/entries/` 接口，使其基于 `Enrollment` 创建课表.
  - [x] 更新冲突检测逻辑，增加对"一对一"类型的检查.
  - [x] 在创建 `ScheduleEntry` 时，填充所有冗余的快照字段.
  - [x] 重构 `GET /api/schedule/entries/` 接口，确保查询和筛选功能正常.

- [x] **D.3.4: 实现智能推荐 API**
  - [x] `GET /api/enrollments/recommendations/`: 创建学习小组时，推荐合适的其他报名记录.
  - [x] `GET /api/schedule/recommendations/`: 按报名记录排课时，推荐可一同上课的报名记录.

### 阶段四：定时任务与业务逻辑 (Scheduled Tasks & Business Logic)

- [x] **D.4.1: 实现课时消耗定时任务**
  - [x] 创建一个每日执行的 Celery 定时任务.
  - [x] 任务逻辑: 查询所有已结束但状态仍为 'scheduled' 的 `ScheduleEntry`，将其更新为 'completed'.

- [x] **D.4.2: 实现课时扣减逻辑**
  - [x] 使用 Django Signals 或重写 `save` 方法，当 `ScheduleEntry` 状态变为 'completed' 时触发.
  - [x] 触发逻辑: 根据 `Attendance` 记录，为出勤学生对应的 `Enrollment` 扣减 `used_lessons`.
  - [x] 课时计算公式: `(end_time - start_time) / duration_minutes`.

### 阶段五：后端测试 (Backend Testing V2)

- [x] **D.5.1: 编写单元测试**
  - [x] 为课时计算和扣减逻辑编写单元测试.
  - [x] 为新的冲突检测逻辑编写单元测试.
- [x] **D.5.2: 编写集成测试**
  - [x] 为所有重构和新增的 API Endpoints 编写集成测试.
  - [x] 为 Celery 课时消耗任务编写测试.

### 阶段六：V2.1 模型与API调整 (V2.1 Model & API Adjustments)

- [x] **D.6.1: 调整数据库模型 (V2.1)**
  - [x] 在 `DataDictionary` 模型中添加 `subgroup` 字段.
  - [x] 在 `Student` 模型中重新添加 `tags` 字段 (关联 `DataDictionary`).
  - [x] 在 `Teacher` 模型中添加 `subjects` 和 `grades` 字段 (关联 `DataDictionary`).
  - [x] 生成并执行数据库迁移.

- [x] **D.6.2: 调整序列化器与API (V2.1)**
  - [x] 更新 `DataDictionarySerializer` 以包含 `subgroup` 字段.
  - [x] 更新 `StudentSerializer` 以支持 `tags` 字段的读写操作.
  - [x] 更新 `TeacherSerializer` 以支持 `subjects` 和 `grades` 字段的读写操作.

- [x] **D.6.3: 调整后端测试 (V2.1)**
  - [x] 更新 `Student` 和 `Teacher` 的CRUD测试，以验证新的关联字段.
  - [x] (可选) 编写测试以验证 `limit_choices_to` 的约束.

---

## 前端开发 (Frontend)

### 阶段七：基础重构 (Basic Refactoring)

- [x] **F.7.1: 更新 API 服务层**
  - [x] 修改 `axios` 封装，使其对接新的 API Endpoints (e.g., `/api/enrollments/`, `/api/course-products/`).
  - [x] 更新所有与后端交互的数据结构 (e.g., `ScheduleEntry` 的结构).

- [x] **F.7.2: 更新状态管理 (Pinia/Vuex)**
  - [x] 调整 store 以适应新的数据模型，例如用 `enrollment` 替代 `teachingClass`.

### 阶段八：页面重构 (UI/UX Refactoring)

- [x] **F.8.1: 基础信息管理页面**
  - [x] 创建 `数据字典` 管理页面.
  - [x] 创建 `课程产品` 管理页面.
  - [x] 创建 `报名记录 (Enrollment)` 管理页面.

- [x] **F.8.2: 核心业务页面**
  - [x] 重构班级管理为 `学习小组 (StudyGroup)` 管理页面.
  - [x] 允许在学习小组中添加或移除报名记录.
  - [x] 在创建学习小组时，调用并展示推荐的报名记录.

- [x] **F.8.3: 重构课表页面**
  - [x] 更新课表视图，以正确展示新的 `ScheduleEntry` 快照数据.
  - [x] 重构创建/编辑课表条目的表单，使其基于 `Enrollment` 或 `StudyGroup` 进行排课.
  - [x] 在排课时，调用并展示推荐一同上课的报名记录.
  - [x] 实现考勤功能：允许用户在课表条目上为学生标记出勤、缺勤、请假状态.

### 阶段九：联调与测试 (Integration & Testing V2)

- [ ] **F.9.1: 前后端接口联调**
  - [ ] 全面测试所有 V2 功能的数据流.
  - [ ] 确保所有表单提交、数据查询、筛选功能正常.

- [ ] **F.9.2: 更新前端组件测试**
  - [ ] 更新或重写关键组件 (如课表视图、排课表单) 的单元测试.