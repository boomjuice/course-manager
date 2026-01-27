"""
Dashboard schemas for role-based dashboard views.

Includes schemas for:
- Student dashboard (schedules, courses, learning records)
- Teacher dashboard (classes, schedules, income)
- Admin dashboard (overview, students, teachers, classes, finance)
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field


# ========== 通用数据结构 ==========

class TimeRangeQuery(BaseModel):
    """时间范围查询参数"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class KpiCard(BaseModel):
    """KPI卡片数据"""
    label: str = Field(..., description="指标名称")
    value: Any = Field(..., description="指标值（可以是数字或字符串）")
    unit: Optional[str] = Field(None, description="单位（如：课时、元、人）")
    trend: Optional[float] = Field(None, description="趋势变化百分比（正数表示增长）")
    is_time_filtered: bool = Field(False, description="是否受时间筛选影响")


class TrendDataPoint(BaseModel):
    """趋势图数据点"""
    date: str = Field(..., description="日期（格式：YYYY-MM-DD 或 YYYY-MM）")
    value: float = Field(..., description="数值")
    label: Optional[str] = Field(None, description="标签（如：周一、1月）")


class DistributionItem(BaseModel):
    """分布图数据项"""
    name: str = Field(..., description="类目名称")
    value: float = Field(..., description="数值")
    color: Optional[str] = Field(None, description="颜色（十六进制，如：#409EFF）")


class RankingItem(BaseModel):
    """排名数据项"""
    rank: int = Field(..., description="排名")
    name: str = Field(..., description="名称")
    value: float = Field(..., description="数值")
    extra: Optional[dict] = Field(None, description="额外信息（如头像、趋势等）")


# ========== 学生仪表盘 ==========

class StudentScheduleItem(BaseModel):
    """学生近期排课项"""
    model_config = ConfigDict(from_attributes=True)

    schedule_id: int = Field(..., description="排课ID")
    schedule_date: date = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    class_plan_id: int = Field(..., description="班级计划ID")
    class_plan_name: str = Field(..., description="班级名称")
    course_name: str = Field(..., description="课程名称")
    teacher_name: Optional[str] = Field(None, description="教师姓名")
    classroom_name: Optional[str] = Field(None, description="教室名称")
    status: str = Field(..., description="排课状态")
    attendance_status: Optional[str] = Field(None, description="出勤状态：normal/leave/absent/None")


class StudentEnrollmentItem(BaseModel):
    """学生报名班级项"""
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: int = Field(..., description="报名ID")
    class_plan_id: int = Field(..., description="班级计划ID")
    class_plan_name: str = Field(..., description="班级名称")
    course_name: str = Field(..., description="课程名称")
    teacher_name: Optional[str] = Field(None, description="主讲教师")
    total_hours: Decimal = Field(..., description="总课时")
    remaining_hours: Decimal = Field(..., description="剩余课时")
    consumed_hours: Decimal = Field(..., description="已消耗课时")
    progress_percent: float = Field(..., description="学习进度百分比")
    status: str = Field(..., description="报名状态")
    enroll_date: date = Field(..., description="报名日期")


class StudentAttendanceRecord(BaseModel):
    """学生出勤记录"""
    model_config = ConfigDict(from_attributes=True)

    attendance_id: int = Field(..., description="出勤记录ID")
    schedule_id: int = Field(..., description="排课ID")
    schedule_date: date = Field(..., description="上课日期")
    class_plan_name: str = Field(..., description="班级名称")
    status: str = Field(..., description="出勤状态：normal/leave/absent")
    leave_reason: Optional[str] = Field(None, description="请假原因")
    deduct_hours: bool = Field(False, description="是否扣课时")


class StudentLessonRecord(BaseModel):
    """学生课时消耗记录"""
    model_config = ConfigDict(from_attributes=True)

    record_id: int = Field(..., description="记录ID")
    record_date: date = Field(..., description="消耗日期")
    hours: Decimal = Field(..., description="消耗课时数")
    class_plan_name: str = Field(..., description="班级名称")
    course_name: str = Field(..., description="课程名称")
    teacher_name: Optional[str] = Field(None, description="授课教师")
    type: str = Field(..., description="消耗类型：schedule/manual/adjustment")
    notes: Optional[str] = Field(None, description="备注")


class StudentDashboardOverview(BaseModel):
    """学生仪表盘概览"""
    # KPI 卡片
    total_remaining_hours: KpiCard = Field(..., description="总剩余课时")
    upcoming_class_count: KpiCard = Field(..., description="近7天课程数")
    attendance_rate: KpiCard = Field(..., description="出勤率")
    active_enrollment_count: KpiCard = Field(..., description="在读班级数")

    # 近期排课（最近7天）
    upcoming_schedules: List[StudentScheduleItem] = Field(
        default_factory=list, description="近期排课列表"
    )


class StudentDashboardCourses(BaseModel):
    """学生我的课程"""
    # 报名班级列表
    enrollments: List[StudentEnrollmentItem] = Field(
        default_factory=list, description="报名班级列表"
    )

    # 课时分布（按课程）
    hours_by_course: List[DistributionItem] = Field(
        default_factory=list, description="课时分布（按课程）"
    )

    # 学习进度趋势
    progress_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="学习进度趋势"
    )


class StudentDashboardRecords(BaseModel):
    """学生学习记录"""
    # 出勤统计
    attendance_summary: dict = Field(
        default_factory=dict,
        description="出勤统计：{total: 总次数, normal: 正常, leave: 请假, absent: 缺勤}"
    )

    # 近期出勤记录
    recent_attendance: List[StudentAttendanceRecord] = Field(
        default_factory=list, description="近期出勤记录"
    )

    # 课时消耗记录
    lesson_records: List[StudentLessonRecord] = Field(
        default_factory=list, description="课时消耗记录"
    )

    # 课时消耗趋势（按月）
    consumption_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="课时消耗趋势"
    )


# ========== 教师仪表盘 ==========

class TeacherScheduleItem(BaseModel):
    """教师近期排课项"""
    model_config = ConfigDict(from_attributes=True)

    schedule_id: int = Field(..., description="排课ID")
    schedule_date: date = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    lesson_hours: float = Field(..., description="课时数")
    class_plan_id: int = Field(..., description="班级计划ID")
    class_plan_name: str = Field(..., description="班级名称")
    course_name: str = Field(..., description="课程名称")
    classroom_name: Optional[str] = Field(None, description="教室名称")
    campus_name: Optional[str] = Field(None, description="校区名称")
    student_count: int = Field(0, description="学生人数")
    status: str = Field(..., description="排课状态")


class TeacherClassItem(BaseModel):
    """教师班级项"""
    model_config = ConfigDict(from_attributes=True)

    class_plan_id: int = Field(..., description="班级计划ID")
    class_plan_name: str = Field(..., description="班级名称")
    course_name: str = Field(..., description="课程名称")
    campus_name: Optional[str] = Field(None, description="校区名称")
    student_count: int = Field(0, description="学生人数")
    total_schedules: int = Field(0, description="总排课数")
    completed_schedules: int = Field(0, description="已完成排课数")
    remaining_schedules: int = Field(0, description="剩余排课数")
    status: str = Field(..., description="班级状态")


class TeacherStudentAttendance(BaseModel):
    """教师视角学生出勤统计"""
    model_config = ConfigDict(from_attributes=True)

    student_id: int = Field(..., description="学生ID")
    student_name: str = Field(..., description="学生姓名")
    total_count: int = Field(0, description="总上课次数")
    normal_count: int = Field(0, description="正常出勤次数")
    leave_count: int = Field(0, description="请假次数")
    absent_count: int = Field(0, description="缺勤次数")
    attendance_rate: float = Field(0.0, description="出勤率")


class TeacherDashboardOverview(BaseModel):
    """教师仪表盘概览"""
    # KPI 卡片
    today_class_count: KpiCard = Field(..., description="今日课程数")
    week_class_count: KpiCard = Field(..., description="本周课程数")
    month_lesson_hours: KpiCard = Field(..., description="本月课时数")
    active_class_count: KpiCard = Field(..., description="在教班级数")

    # 近期排课（未来7天）
    upcoming_schedules: List[TeacherScheduleItem] = Field(
        default_factory=list, description="近期排课列表"
    )

    # 今日排课
    today_schedules: List[TeacherScheduleItem] = Field(
        default_factory=list, description="今日排课列表"
    )


class TeacherDashboardClasses(BaseModel):
    """教师教学情况"""
    # 授课班级列表
    classes: List[TeacherClassItem] = Field(
        default_factory=list, description="授课班级列表"
    )

    # 学生出勤统计
    student_attendance: List[TeacherStudentAttendance] = Field(
        default_factory=list, description="学生出勤统计"
    )

    # 班级学生分布
    students_by_class: List[DistributionItem] = Field(
        default_factory=list, description="班级学生分布"
    )


class TeacherDashboardIncome(BaseModel):
    """教师课时收入"""
    # KPI
    month_income: KpiCard = Field(..., description="本月预估收入")
    month_hours: KpiCard = Field(..., description="本月已授课时")
    hourly_rate: KpiCard = Field(..., description="课时单价")

    # 收入趋势（按月）
    income_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="收入趋势"
    )

    # 课时趋势（按月）
    hours_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="课时趋势"
    )

    # 课时分布（按班级）
    hours_by_class: List[DistributionItem] = Field(
        default_factory=list, description="课时分布（按班级）"
    )


# ========== 管理员仪表盘 ==========

class AdminDashboardOverview(BaseModel):
    """管理员仪表盘概览"""
    # KPI 卡片
    total_students: KpiCard = Field(..., description="学生总数")
    total_teachers: KpiCard = Field(..., description="教师总数")
    active_classes: KpiCard = Field(..., description="进行中班级数")
    month_revenue: KpiCard = Field(..., description="本月收入")

    # 今日数据
    today_schedules: int = Field(0, description="今日排课数")
    today_new_enrollments: int = Field(0, description="今日新报名数")

    # 近7天排课趋势
    schedule_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="排课趋势"
    )

    # 近7天报名趋势
    enrollment_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="报名趋势"
    )


class AdminDashboardStudents(BaseModel):
    """管理员学生分析"""
    # KPI
    total_count: KpiCard = Field(..., description="学生总数")
    active_count: KpiCard = Field(..., description="在读学生数")
    new_this_month: KpiCard = Field(..., description="本月新增学生")
    avg_remaining_hours: KpiCard = Field(..., description="平均剩余课时")

    # 学生来源分布
    source_distribution: List[DistributionItem] = Field(
        default_factory=list, description="来源分布"
    )

    # 年级分布
    grade_distribution: List[DistributionItem] = Field(
        default_factory=list, description="年级分布"
    )

    # 课时消耗排名
    consumption_ranking: List[RankingItem] = Field(
        default_factory=list, description="课时消耗排名"
    )

    # 学生增长趋势
    growth_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="学生增长趋势"
    )


class AdminDashboardTeachers(BaseModel):
    """管理员教师分析"""
    # KPI
    total_count: KpiCard = Field(..., description="教师总数")
    active_count: KpiCard = Field(..., description="在职教师数")
    avg_class_count: KpiCard = Field(..., description="平均授课班级数")
    avg_monthly_hours: KpiCard = Field(..., description="平均月课时")

    # 科目分布
    subject_distribution: List[DistributionItem] = Field(
        default_factory=list, description="科目分布"
    )

    # 课时排名
    hours_ranking: List[RankingItem] = Field(
        default_factory=list, description="课时排名"
    )

    # 教师工作量分布
    workload_distribution: List[DistributionItem] = Field(
        default_factory=list, description="工作量分布"
    )


class AdminDashboardClasses(BaseModel):
    """管理员班级分析"""
    # KPI
    total_count: KpiCard = Field(..., description="班级总数")
    active_count: KpiCard = Field(..., description="进行中班级数")
    avg_student_count: KpiCard = Field(..., description="平均班级人数")
    completion_rate: KpiCard = Field(..., description="班级完成率")

    # 班级状态分布
    status_distribution: List[DistributionItem] = Field(
        default_factory=list, description="状态分布"
    )

    # 课程类型分布
    course_distribution: List[DistributionItem] = Field(
        default_factory=list, description="课程分布"
    )

    # 热门班级排名（按学生数）
    popular_ranking: List[RankingItem] = Field(
        default_factory=list, description="热门班级排名"
    )

    # 排课完成度趋势
    completion_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="完成度趋势"
    )


class AdminDashboardFinance(BaseModel):
    """管理员财务分析"""
    # KPI
    month_revenue: KpiCard = Field(..., description="本月收入")
    month_expense: KpiCard = Field(..., description="本月支出（课时费）")
    month_profit: KpiCard = Field(..., description="本月毛利")
    avg_enrollment_amount: KpiCard = Field(..., description="平均报名金额")

    # 收入趋势（按月）
    revenue_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="收入趋势"
    )

    # 支出趋势（按月）
    expense_trend: List[TrendDataPoint] = Field(
        default_factory=list, description="支出趋势"
    )

    # 收入来源分布（按课程类型）
    revenue_by_course: List[DistributionItem] = Field(
        default_factory=list, description="收入来源分布"
    )

    # 校区收入分布
    revenue_by_campus: List[DistributionItem] = Field(
        default_factory=list, description="校区收入分布"
    )


# ========== 导出所有 Schema ==========

__all__ = [
    # 通用数据结构
    "TimeRangeQuery",
    "KpiCard",
    "TrendDataPoint",
    "DistributionItem",
    "RankingItem",
    # 学生仪表盘
    "StudentScheduleItem",
    "StudentEnrollmentItem",
    "StudentAttendanceRecord",
    "StudentLessonRecord",
    "StudentDashboardOverview",
    "StudentDashboardCourses",
    "StudentDashboardRecords",
    # 教师仪表盘
    "TeacherScheduleItem",
    "TeacherClassItem",
    "TeacherStudentAttendance",
    "TeacherDashboardOverview",
    "TeacherDashboardClasses",
    "TeacherDashboardIncome",
    # 管理员仪表盘
    "AdminDashboardOverview",
    "AdminDashboardStudents",
    "AdminDashboardTeachers",
    "AdminDashboardClasses",
    "AdminDashboardFinance",
]
