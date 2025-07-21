# 首页仪表盘 (Dashboard) 开发任务列表

## Phase 1: 后端 API 开发 (Django)

- [x] 1.1. 创建后端 API 路由 (`/api/dashboard/stats/`) 和视图基本结构 (`DashboardStatsView`)。
- [x] 1.2. 在 `DashboardStatsView` 中实现核心逻辑，根据 `start_date` 和 `end_date` 从 `ScheduleEntry` 模型中筛选数据。
- [x] 1.3. 实现 **管理员 (Admin)** 角色的数据聚合逻辑。
- [x] 1.4. 实现 **教师 (Teacher)** 角色的数据聚合逻辑。
- [x] 1.5. 实现 **学生 (Student)** 角色的数据聚合逻辑。
- [x] 1.6. 编写单元测试 (`api/tests.py`)，覆盖三种角色和不同日期范围下的 API 返回数据。

## Phase 2: 前端页面开发 (Vue)

- [x] 2.1. 创建 `frontend/src/views/DashboardView.vue` 文件，并设置基础布局。
- [x] 2.2. 在 `DashboardView.vue` 中添加 Element Plus 的日期范围选择器，并实现获取后端数据的逻辑。
- [x] 2.3. 安装 `echarts` 依赖，并创建一个可复用的图表组件 `frontend/src/components/charts/BaseChart.vue`。
- [x] 2.4. 开发 **管理员 (Admin)** 仪表盘界面，包括 KPI 卡片和图表。
- [x] 2.5. 开发 **教师 (Teacher)** 仪表盘界面。
- [x] 2.6. 开发 **学生 (Student)** 仪表盘界面。
- [x] 2.7. 更新前端路由 (`frontend/src/router/index.ts`)，将 `/` 指向 `DashboardView`。

## Phase 3: 收尾

- [x] 3.1. 代码整体审查和清理。
- [x] 3.2. 确认所有任务完成并更新此 TODO list。
