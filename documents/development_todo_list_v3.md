# V3 功能迭代：开班计划 (Course Offering)

## 后端开发 (Backend)

### 阶段一：数据库模型与迁移

- [x] **D.1.1: 创建 `CourseOffering` 模型**
  - [x] 在 `api/models.py` 中定义 `CourseOffering` 模型，包含 `course_product`, `name`, `start_date`, `end_date`, `status` 字段。

- [x] **D.1.2: 调整 `Enrollment` 模型**
  - [x] 移除 `Enrollment` 模型中对 `CourseProduct` 的直接外键关联。
  - [x] 添加 `Enrollment` 模型对 `CourseOffering` 的新外键关联。

- [x] **D.1.3: 生成数据库迁移**
  - [x] 运行 `makemigrations` 为新的模型和字段变更创建迁移文件。

- [x] **D.1.4: 编写数据迁移脚本 (关键步骤)**
  - [x] 创建一个空的迁移文件。
  - [x] 编写 `RunPython` 脚本，为每一个现有的 `Enrollment` 记录，自动创建一个对应的 `CourseOffering` 记录，并将 `Enrollment` 与之关联。
    *   *测试策略*: 这个脚本需要仔细设计，以确保现有数据能平滑过渡。

- [x] **D.1.5: 执行迁移**
  - [x] 运行 `migrate` 应用所有变更。

### 阶段二：API 调整与开发

- [x] **D.2.1: 创建 `CourseOffering` API**
  - [x] 在 `api/serializers.py` 中创建 `CourseOfferingSerializer`。
  - [x] 在 `api/views.py` 中创建 `CourseOfferingViewSet` (支持 CRUD 和筛选)。

- [x] **D.2.2: 调整 `Enrollment` API**
  - [x] 更新 `EnrollmentSerializer` 以反映新的外键关系（关联 `CourseOffering`）。
  - [x] 更新 `EnrollmentViewSet` 的筛选和创建/更新逻辑。

- [x] **D.2.3: 调整排课 API (`ScheduleEntry`)**
  - [x] 更新 `ScheduleEntryCreateUpdateSerializer` 的 `validate` 方法，增加验证逻辑：确保排课的日期 (`start_time`) 必须在所选报名记录关联的 `CourseOffering` 的 `start_date` 和 `end_date` 之间。

### 阶段三：后端测试

- [x] **D.3.1: 编写模型与 API 单元测试**
  - [x] 为 `CourseOffering` API 的 CRUD 和筛选功能编写单元测试。
  - [x] 更新 `Enrollment` API 的测试，以验证新的关联关系。
  - [x] **(关键测试)** 为排课的日期范围验证逻辑编写专门的单元测试，覆盖边界条件（例如，正好在开始/结束日期排课，或在范围之外排课）。

---

## 前端开发 (Frontend)

### 阶段四：基础页面与组件

- [x] **F.4.1: 创建“开班计划”管理页面**
  - [x] 创建 `CourseOfferingListView.vue` 视图文件。
  - [x] 创建 `CourseOfferingForm.vue` 组件，用于新建/编辑开班计划。
  - [x] 在主布局和路由中添加入口。

- [x] **F.4.2: 重构“报名管理”页面**
  - [x] 修改 `EnrollmentListView.vue`，使其筛选和展示都围绕“开班计划”。
  - [x] 修改 `EnrollmentForm.vue`，将选择“课程产品”改为选择“开班计划”。

- [x] **F.4.3: 重构排课表单**
  - [x] 修改 `NewScheduleEntryForm.vue` 和 `BatchScheduleForm.vue`。
  - [x] 将选择“课程产品”改为选择“开班计划”。
  - [x] (可选) 在日期选择器中，可以根据所选的开班计划禁用无效的日期范围。