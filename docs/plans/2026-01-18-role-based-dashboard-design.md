# 角色化仪表盘设计文档

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重新设计仪表盘系统，支持按角色（学生/教师/管理员）展示不同内容，支持时间范围过滤。

**Architecture:** 前端根据用户角色渲染不同的仪表盘组件，所有角色使用统一的标签页布局和视觉风格。后端按角色拆分 API 端点，支持时间范围和校区过滤参数。

**Tech Stack:** FastAPI + SQLAlchemy (后端), Vue 3 + Element Plus + ECharts (前端)

---

## 1. 整体架构

### 1.1 角色与数据范围

| 角色 | 数据范围 | 特殊能力 |
|------|----------|----------|
| 学生 (student) | 仅看自己的数据 | 无 |
| 教师 (teacher) | 仅看自己带的班级/学生数据 | 无 |
| 校区管理员 (campus_admin) | 仅看所属校区的数据 | 无 |
| 超级管理员 (super_admin) | 默认看全部数据 | 可切换校区、跨校区对比分析 |

### 1.2 统一交互规范

- **布局**：所有角色都使用标签页 (Tab) 布局
- **时间过滤**：顶部提供时间范围选择器（固定选项 + 自定义日期）
- **数据刷新**：切换 Tab 时自动刷新 + 手动刷新按钮
- **视觉风格**：三种角色的卡片、图表、配色保持一致

### 1.3 时间过滤规则

- **状态型指标**（不受时间过滤）：在读学生数、进行中班级数、剩余课时等
- **时间型指标**（受时间过滤）：新增报名、收入、课时消耗、出勤统计等

### 1.4 时间范围选项

**固定选项：**
- 今日
- 本周
- 本月
- 近7天
- 近30天
- 近90天

**自定义：**
- 日期范围选择器，用户可选择任意开始和结束日期

---

## 2. 学生仪表盘

### 2.1 Tab 结构

| Tab | 内容 |
|-----|------|
| **概览** | 核心 KPI 卡片 + 近期排课日历/列表 |
| **我的课程** | 报名班级列表 + 各班级详情 |
| **学习记录** | 出勤记录 + 课时消耗明细 |

### 2.2 概览 Tab

**KPI 卡片（状态型，不受时间过滤）：**
- 剩余课时（`Student.remaining_hours`）
- 已用课时（`Student.total_hours - remaining_hours`）
- 报名班级数（关联 `Enrollment` 数量，status=active）
- 累计付款（`Student.total_paid`）

**近期排课（时间型）：**
- 展示未来 7 天的上课安排
- 信息：日期、时间、班级名、教师、教室
- 来源：通过 `Enrollment` → `ClassPlan` → `Schedule` 关联查询

### 2.3 我的课程 Tab

**报名班级列表：**
- 班级名、课程名、教师、上课时间、状态
- 购买课时、已用课时、剩余课时（按班级拆分）
- 支持展开查看班级详情

### 2.4 学习记录 Tab

**出勤记录（时间型，支持过滤）：**
- 日期、班级、状态（正常/请假/缺勤）、备注
- 出勤统计：出勤率、请假次数、缺勤次数

**课时消耗明细（时间型）：**
- 日期、班级、消耗课时、类型（上课/手动调整/退费）
- 课时消耗趋势图（按周/月）

---

## 3. 教师仪表盘

### 3.1 Tab 结构

| Tab | 内容 |
|-----|------|
| **概览** | 核心 KPI 卡片 + 近期排课列表 |
| **教学情况** | 我的班级 + 学生管理 + 出勤统计 |
| **课时收入** | 课时统计 + 课时费预估/历史 |

### 3.2 概览 Tab

**KPI 卡片（状态型，不受时间过滤）：**
- 带班数量（关联 `ClassPlan` 中 `teacher_id` = 我，status=ongoing）
- 学生总数（通过 `ClassPlan` → `Enrollment` 去重统计）

**KPI 卡片（时间型）：**
- 本月已上课时（`Schedule` 中 status=completed 的 `lesson_hours` 求和）
- 本月预估收入（已上课时 × `Teacher.hourly_rate`）

**近期排课（时间型）：**
- 展示未来 7 天的授课安排
- 信息：日期、时间、班级名、教室、学生人数
- 来源：`Schedule` 表 where `teacher_id` = 我

### 3.3 教学情况 Tab

**我的班级列表：**
- 班级名、课程名、状态、学生人数/最大人数（上座率）
- 进度：已完成课次/总课次
- 支持展开查看班级学生名单

**学生出勤统计（时间型）：**
- 各班级出勤率、请假率、缺勤率
- 出勤异常学生提醒（缺勤率高的学生）

### 3.4 课时收入 Tab

**课时统计（时间型）：**
- 本周/本月/自定义时间范围内的上课课时数
- 按班级拆分的课时明细
- 课时趋势图（按周/月）

**课时费统计（时间型）：**
- 预估收入 = 课时数 × 课时费单价
- 历史收入趋势（如果系统有结算记录的话）

---

## 4. 管理员仪表盘

### 4.1 Tab 结构

| Tab | 内容 |
|-----|------|
| **概览** | 核心 KPI + 关键趋势图 |
| **学生** | 学生统计 + 分布分析 |
| **教师** | 教师统计 + 工作量分析 |
| **班级** | 班级统计 + 运营分析 |
| **财务** | 收入统计 + 课时销售分析 |

### 4.2 超管专属功能

- 顶部增加**校区切换器**（下拉选择：全部 / 北京校区 / 上海校区...）
- **概览 Tab** 增加"校区对比"图表

### 4.3 概览 Tab

**KPI 卡片（状态型）：**
- 在读学生数（`Student` where status=active）
- 授课教师数（`Teacher` where status=active）
- 进行中班级（`ClassPlan` where status=ongoing）
- 课程产品数（`Course` where is_active=true）

**KPI 卡片（时间型）：**
- 新增报名（`Enrollment` 按时间范围过滤）
- 新增学生（`Student` 按 created_time 过滤）
- 期间收入（`Enrollment.paid_amount` 求和）
- 课时消耗（`LessonRecord.hours` 求和）

**趋势图表：**
- 报名趋势（折线图：报名人数 + 报名金额，双 Y 轴）
- 收入趋势（柱状图：按日/周/月）

**超管专属 - 校区对比（选择"全部"校区时显示）：**
- 各校区学生数对比（柱状图）
- 各校区收入对比（柱状图）

### 4.4 学生 Tab

**KPI 卡片（状态型）：**
- 在读学生数
- 总剩余课时（所有学生 `remaining_hours` 求和）
- 平均剩余课时（剩余课时 / 在读学生数）

**KPI 卡片（时间型）：**
- 新增学生数
- 流失学生数（状态变为 paused/graduated 的）

**分布图表：**
- 学生状态分布（饼图：在读/毕业/暂停）
- 学生来源渠道分布（饼图：转介绍/网络/活动...）
- 学生年级分布（柱状图）
- 新增学生趋势（折线图，时间型）

### 4.5 教师 Tab

**KPI 卡片（状态型）：**
- 在职教师数
- 平均带班数（总进行中班级 / 教师数）

**KPI 卡片（时间型）：**
- 总授课课时（`Schedule` completed 的 `lesson_hours`）
- 平均授课课时（总课时 / 教师数）

**分布图表：**
- 教师状态分布（饼图：在职/休假/离职）
- 教师科目分布（柱状图，来自 `Teacher.subjects`）
- 教师工作量排名（横向柱状图：Top 10 课时最多的教师）

### 4.6 班级 Tab

**KPI 卡片（状态型）：**
- 进行中班级数
- 待开班数量（status=pending）
- 平均上座率（`current_students / max_students` 平均值）

**KPI 卡片（时间型）：**
- 新开班数量
- 结业班级数量

**分布图表：**
- 班级状态分布（饼图：待开班/进行中/已结束/已取消）
- 班级上座率分布（柱状图：按区间 0-50%/50-80%/80-100%）
- 各科目班级数量（柱状图）
- 班级完课进度（横向柱状图：Top 10 进度最快/最慢的班级）

### 4.7 财务 Tab

**KPI 卡片（时间型，全部受时间过滤）：**
- 总收入（`Enrollment.paid_amount` 求和）
- 报名人次
- 客单价（总收入 / 报名人次）
- 课时销售量（`Enrollment.purchased_hours` 求和）

**KPI 卡片（状态型）：**
- 总剩余课时价值（剩余课时 × 平均单价，预估）

**分布图表：**
- 收入趋势（折线图/柱状图，按日/周/月）
- 收入按科目分布（饼图）
- 收入按校区分布（超管专属，饼图）
- 课时消耗率趋势（折线图：已用课时 / 已购课时）

---

## 5. 技术实现方案

### 5.1 后端 API 设计

**重构现有 Dashboard API，按角色拆分：**

```
GET /api/v1/dashboard/student          # 学生仪表盘数据
GET /api/v1/dashboard/student/courses  # 学生-我的课程
GET /api/v1/dashboard/student/records  # 学生-学习记录

GET /api/v1/dashboard/teacher          # 教师仪表盘数据
GET /api/v1/dashboard/teacher/classes  # 教师-教学情况
GET /api/v1/dashboard/teacher/income   # 教师-课时收入

GET /api/v1/dashboard/admin            # 管理员-概览
GET /api/v1/dashboard/admin/students   # 管理员-学生分析
GET /api/v1/dashboard/admin/teachers   # 管理员-教师分析
GET /api/v1/dashboard/admin/classes    # 管理员-班级分析
GET /api/v1/dashboard/admin/finance    # 管理员-财务分析
```

**通用查询参数：**
- `start_date`: 开始日期（可选，格式：YYYY-MM-DD）
- `end_date`: 结束日期（可选，格式：YYYY-MM-DD）
- `campus_id`: 校区ID（超管专用，可选）

### 5.2 前端实现方案

**路由设计：**
- 统一入口 `/dashboard`，根据用户角色渲染不同组件

**组件结构：**
```
views/Dashboard/
├── DashboardView.vue          # 入口，根据角色分发
├── StudentDashboard.vue       # 学生仪表盘
├── TeacherDashboard.vue       # 教师仪表盘
├── AdminDashboard.vue         # 管理员仪表盘
└── components/
    ├── TimeRangeSelector.vue  # 时间范围选择器（复用）
    ├── KpiCard.vue            # KPI 卡片（复用）
    ├── TrendChart.vue         # 趋势图表（复用）
    ├── DistributionChart.vue  # 分布图表（复用）
    └── DataTable.vue          # 数据表格（复用）
```

**时间范围选择器：**
- 固定选项：今日 / 本周 / 本月 / 近7天 / 近30天 / 近90天
- 自定义：Element Plus 的 `el-date-picker` range 模式
- 选择后触发数据刷新

**状态管理：**
- 使用 Pinia 存储当前选中的时间范围
- 各 Tab 组件监听时间范围变化，自动刷新时间型指标

---

## 6. 数据模型依赖

### 6.1 学生仪表盘数据来源

- `Student` - 学生基本信息、课时统计
- `Enrollment` - 报名记录
- `ClassPlan` - 班级信息
- `Schedule` - 排课信息
- `StudentAttendance` - 出勤记录
- `LessonRecord` - 课时消耗记录

### 6.2 教师仪表盘数据来源

- `Teacher` - 教师基本信息、课时费
- `ClassPlan` - 带班信息
- `Schedule` - 排课信息
- `Enrollment` - 学生报名（用于统计学生数）
- `StudentAttendance` - 学生出勤

### 6.3 管理员仪表盘数据来源

- `Student` - 学生统计
- `Teacher` - 教师统计
- `Course` - 课程统计
- `ClassPlan` - 班级统计
- `Enrollment` - 报名和财务统计
- `Schedule` - 排课统计
- `LessonRecord` - 课时消耗统计
- `Campus` - 校区信息（超管切换）

---

## 7. 实施优先级建议

1. **Phase 1 - 基础框架**
   - 后端 API 骨架搭建
   - 前端路由和组件结构
   - 时间范围选择器组件

2. **Phase 2 - 管理员仪表盘**
   - 先做管理员仪表盘（内容最多，可验证整体架构）
   - 5 个 Tab 逐个实现

3. **Phase 3 - 学生/教师仪表盘**
   - 复用管理员仪表盘的组件
   - 调整数据查询逻辑

4. **Phase 4 - 优化和测试**
   - 性能优化（缓存、懒加载）
   - 响应式适配
   - 完整测试
