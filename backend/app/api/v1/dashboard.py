"""
Dashboard API endpoints - statistics and overview data.
包含管理员统计数据和学生个人仪表盘。
"""
from typing import Optional, List
from datetime import datetime, timedelta, date
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date, and_, Integer
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DBSession, CampusScopedQuery
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class_plan import ClassPlan
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.schedule import Schedule
from app.models.student_attendance import StudentAttendance
from app.models.lesson_record import LessonRecord
from app.schemas.common import success_response
from app.schemas.dashboard import (
    KpiCard,
    StudentDashboardOverview,
    StudentDashboardCourses,
    StudentDashboardRecords,
    StudentScheduleItem,
    StudentEnrollmentItem,
    StudentAttendanceRecord,
    StudentLessonRecord,
)

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    active_students: int
    total_teachers: int
    active_class_plans: int
    total_courses: int
    total_enrollments: int
    recent_enrollments: int


class RecentActivity(BaseModel):
    """Recent activity item."""
    type: str
    title: str
    time: datetime
    description: Optional[str] = None


class TrendDataPoint(BaseModel):
    """日期趋势数据点"""
    date: str
    count: int
    amount: float = 0


class ClassPlanEnrollmentStat(BaseModel):
    """班级报名统计"""
    class_plan_id: int
    class_plan_name: str
    enrollment_count: int
    total_amount: float


class ChartDataResponse(BaseModel):
    """图表数据响应"""
    enrollment_trend: List[TrendDataPoint]  # 报名趋势
    class_plan_stats: List[ClassPlanEnrollmentStat]  # 班级报名统计


@router.get("/stats", summary="获取仪表盘统计数据")
async def get_dashboard_stats(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Get dashboard statistics.
    """
    # Count active students
    active_students = (await db.execute(
        select(func.count()).select_from(Student).where(Student.status == "active")
    )).scalar() or 0

    # Count teachers
    total_teachers = (await db.execute(
        select(func.count()).select_from(Teacher)
    )).scalar() or 0

    # Count active class plans
    active_class_plans = (await db.execute(
        select(func.count()).select_from(ClassPlan).where(ClassPlan.status == "active")
    )).scalar() or 0

    # Count courses
    total_courses = (await db.execute(
        select(func.count()).select_from(Course)
    )).scalar() or 0

    # Count enrollments
    total_enrollments = (await db.execute(
        select(func.count()).select_from(Enrollment)
    )).scalar() or 0

    # Recent enrollments (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_enrollments = (await db.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.created_time >= week_ago
        )
    )).scalar() or 0

    return success_response(DashboardStats(
        active_students=active_students,
        total_teachers=total_teachers,
        active_class_plans=active_class_plans,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        recent_enrollments=recent_enrollments,
    ).model_dump())


@router.get("/charts", summary="获取图表数据")
async def get_chart_data(
    current_user: CurrentUser,
    db: DBSession,
    days: int = Query(30, ge=7, le=90, description="趋势天数"),
):
    """
    获取仪表盘图表数据：
    - enrollment_trend: 最近N天报名趋势（每日报名数和金额）
    - class_plan_stats: 各班级报名人数和总金额统计
    """
    # 1. 报名趋势数据（最近N天）
    start_date = datetime.utcnow().date() - timedelta(days=days - 1)

    # 查询每日报名数据
    enrollment_by_date = await db.execute(
        select(
            cast(Enrollment.created_time, Date).label("enroll_date"),
            func.count(Enrollment.id).label("count"),
            func.sum(Enrollment.paid_amount).label("amount")
        )
        .where(Enrollment.created_time >= datetime.combine(start_date, datetime.min.time()))
        .group_by(cast(Enrollment.created_time, Date))
        .order_by(cast(Enrollment.created_time, Date))
    )
    enrollment_data = {row.enroll_date: (row.count, float(row.amount or 0)) for row in enrollment_by_date}

    # 补齐所有日期（没有数据的日期填0）
    enrollment_trend = []
    current = start_date
    today = datetime.utcnow().date()
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        count, amount = enrollment_data.get(current, (0, 0))
        enrollment_trend.append(TrendDataPoint(date=date_str, count=count, amount=amount))
        current += timedelta(days=1)

    # 2. 各班级报名统计（只统计进行中的班级，限制前10个）
    class_plan_stats_query = await db.execute(
        select(
            ClassPlan.id,
            ClassPlan.name,
            func.count(Enrollment.id).label("enrollment_count"),
            func.sum(Enrollment.paid_amount).label("total_amount")
        )
        .join(Enrollment, Enrollment.class_plan_id == ClassPlan.id)
        .where(ClassPlan.is_active == True)
        .group_by(ClassPlan.id, ClassPlan.name)
        .order_by(func.count(Enrollment.id).desc())
        .limit(10)
    )

    class_plan_stats = [
        ClassPlanEnrollmentStat(
            class_plan_id=row.id,
            class_plan_name=row.name,
            enrollment_count=row.enrollment_count,
            total_amount=float(row.total_amount or 0)
        )
        for row in class_plan_stats_query
    ]

    return success_response(ChartDataResponse(
        enrollment_trend=enrollment_trend,
        class_plan_stats=class_plan_stats,
    ).model_dump())


# ========== 学生仪表盘端点 ==========

async def _get_student_for_user(db: DBSession, user_id: int) -> Student:
    """
    根据用户ID获取关联的学生记录。
    学生通过 Student.user_id 关联到用户账号。
    """
    result = await db.execute(
        select(Student).where(Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundException("未找到关联的学生记录")
    return student


def _require_student_role(current_user, scope: CampusScopedQuery):
    """
    检查当前用户是否是学生角色。
    如果不是学生角色，抛出 403 错误。
    """
    role_code = scope.get_token_role_code(current_user)
    if role_code != "student":
        raise ForbiddenException("此接口仅供学生访问")


@router.get("/student", summary="学生仪表盘概览")
async def get_student_dashboard_overview(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    获取学生仪表盘概览数据。
    包含：
    - KPI卡片：总剩余课时、近7天课程数、出勤率、在读班级数
    - 近期排课列表（未来7天）
    """
    scope = CampusScopedQuery()
    _require_student_role(current_user, scope)

    # 获取学生记录
    student = await _get_student_for_user(db, current_user.id)

    today = date.today()
    next_week = today + timedelta(days=7)

    # 1. 查询学生的活跃报名
    enrollment_result = await db.execute(
        select(Enrollment)
        .options(
            selectinload(Enrollment.class_plan).selectinload(ClassPlan.course),
            selectinload(Enrollment.class_plan).selectinload(ClassPlan.teacher),
        )
        .where(
            and_(
                Enrollment.student_id == student.id,
                Enrollment.status == "active",
            )
        )
    )
    enrollments = enrollment_result.scalars().all()
    enrollment_ids = [e.id for e in enrollments]
    class_plan_ids = [e.class_plan_id for e in enrollments]

    # 2. 计算总剩余课时
    total_remaining = sum(
        (e.purchased_hours - e.used_hours) for e in enrollments
    )

    # 3. 查询近期排课（未来7天）
    upcoming_schedules = []
    if class_plan_ids:
        schedule_result = await db.execute(
            select(Schedule)
            .options(
                selectinload(Schedule.class_plan).selectinload(ClassPlan.course),
                selectinload(Schedule.class_plan).selectinload(ClassPlan.teacher),
                selectinload(Schedule.teacher),
                selectinload(Schedule.classroom),
            )
            .where(
                and_(
                    Schedule.class_plan_id.in_(class_plan_ids),
                    Schedule.schedule_date >= today,
                    Schedule.schedule_date <= next_week,
                    Schedule.status != "cancelled",
                )
            )
            .order_by(Schedule.schedule_date, Schedule.start_time)
        )
        schedules = schedule_result.scalars().all()

        # 查询学生在这些排课的出勤状态
        schedule_ids = [s.id for s in schedules]
        attendance_map = {}
        if schedule_ids and enrollment_ids:
            attendance_result = await db.execute(
                select(StudentAttendance)
                .where(
                    and_(
                        StudentAttendance.schedule_id.in_(schedule_ids),
                        StudentAttendance.enrollment_id.in_(enrollment_ids),
                    )
                )
            )
            for att in attendance_result.scalars().all():
                attendance_map[att.schedule_id] = att.status

        for schedule in schedules:
            class_plan = schedule.class_plan
            teacher = schedule.teacher or (class_plan.teacher if class_plan else None)
            course = class_plan.course if class_plan else None

            upcoming_schedules.append(StudentScheduleItem(
                schedule_id=schedule.id,
                schedule_date=schedule.schedule_date,
                start_time=schedule.start_time,
                end_time=schedule.end_time,
                class_plan_id=schedule.class_plan_id,
                class_plan_name=class_plan.name if class_plan else "",
                course_name=course.name if course else "",
                teacher_name=teacher.name if teacher else None,
                classroom_name=schedule.classroom.name if schedule.classroom else None,
                status=schedule.status,
                attendance_status=attendance_map.get(schedule.id),
            ))

    # 4. 计算出勤率
    attendance_rate = 0.0
    if enrollment_ids:
        # 获取所有出勤记录
        attendance_stats_result = await db.execute(
            select(
                func.count(StudentAttendance.id).label("total"),
                func.sum(
                    func.cast(StudentAttendance.status == "normal", Integer)
                ).label("normal_count"),
            )
            .where(StudentAttendance.enrollment_id.in_(enrollment_ids))
        )
        stats = attendance_stats_result.first()
        if stats and stats.total > 0:
            attendance_rate = round((stats.normal_count or 0) / stats.total * 100, 1)

    # 构建响应
    response = StudentDashboardOverview(
        total_remaining_hours=KpiCard(
            label="剩余课时",
            value=float(total_remaining),
            unit="课时",
        ),
        upcoming_class_count=KpiCard(
            label="近7天课程",
            value=len(upcoming_schedules),
            unit="节",
        ),
        attendance_rate=KpiCard(
            label="出勤率",
            value=attendance_rate,
            unit="%",
        ),
        active_enrollment_count=KpiCard(
            label="在读班级",
            value=len(enrollments),
            unit="个",
        ),
        upcoming_schedules=upcoming_schedules,
    )

    return success_response(response.model_dump())


@router.get("/student/courses", summary="学生我的课程")
async def get_student_courses(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    获取学生报名的班级列表。
    包含每个班级的课时进度、教师信息等。
    """
    scope = CampusScopedQuery()
    _require_student_role(current_user, scope)

    # 获取学生记录
    student = await _get_student_for_user(db, current_user.id)

    # 查询学生的所有报名
    enrollment_result = await db.execute(
        select(Enrollment)
        .options(
            selectinload(Enrollment.class_plan).selectinload(ClassPlan.course),
            selectinload(Enrollment.class_plan).selectinload(ClassPlan.teacher),
        )
        .where(Enrollment.student_id == student.id)
        .order_by(Enrollment.created_time.desc())
    )
    enrollments = enrollment_result.scalars().all()

    enrollment_items = []
    for e in enrollments:
        class_plan = e.class_plan
        course = class_plan.course if class_plan else None
        teacher = class_plan.teacher if class_plan else None

        total = float(e.purchased_hours)
        used = float(e.used_hours)
        remaining = total - used
        progress = round((used / total * 100) if total > 0 else 0, 1)

        enrollment_items.append(StudentEnrollmentItem(
            enrollment_id=e.id,
            class_plan_id=e.class_plan_id,
            class_plan_name=class_plan.name if class_plan else "",
            course_name=course.name if course else "",
            teacher_name=teacher.name if teacher else None,
            total_hours=e.purchased_hours,
            remaining_hours=Decimal(str(remaining)),
            consumed_hours=e.used_hours,
            progress_percent=progress,
            status=e.status,
            enroll_date=e.enroll_date or date.today(),
        ))

    response = StudentDashboardCourses(
        enrollments=enrollment_items,
        hours_by_course=[],  # 可以后续扩展
        progress_trend=[],   # 可以后续扩展
    )

    return success_response(response.model_dump())


@router.get("/student/records", summary="学生学习记录")
async def get_student_records(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    """
    获取学生的出勤和课时消耗记录。
    支持按时间范围过滤。
    """
    scope = CampusScopedQuery()
    _require_student_role(current_user, scope)

    # 获取学生记录
    student = await _get_student_for_user(db, current_user.id)

    # 获取学生的所有报名ID
    enrollment_result = await db.execute(
        select(Enrollment.id, Enrollment.class_plan_id)
        .where(Enrollment.student_id == student.id)
    )
    enrollment_rows = enrollment_result.all()
    enrollment_ids = [r.id for r in enrollment_rows]
    enrollment_class_plan_map = {r.id: r.class_plan_id for r in enrollment_rows}

    if not enrollment_ids:
        # 没有报名记录，返回空数据
        return success_response(StudentDashboardRecords(
            attendance_summary={"total": 0, "normal": 0, "leave": 0, "absent": 0},
            recent_attendance=[],
            lesson_records=[],
            consumption_trend=[],
        ).model_dump())

    # 1. 查询出勤记录
    attendance_query = (
        select(StudentAttendance)
        .options(
            selectinload(StudentAttendance.schedule),
            selectinload(StudentAttendance.enrollment).selectinload(Enrollment.class_plan),
        )
        .where(StudentAttendance.enrollment_id.in_(enrollment_ids))
    )

    attendance_result = await db.execute(attendance_query)
    attendances = attendance_result.scalars().all()

    # 出勤统计
    attendance_summary = {"total": 0, "normal": 0, "leave": 0, "absent": 0}
    recent_attendance = []

    for att in attendances:
        attendance_summary["total"] += 1
        if att.status == "normal":
            attendance_summary["normal"] += 1
        elif att.status == "leave":
            attendance_summary["leave"] += 1
        elif att.status == "absent":
            attendance_summary["absent"] += 1

        schedule = att.schedule
        class_plan = att.enrollment.class_plan if att.enrollment else None

        recent_attendance.append(StudentAttendanceRecord(
            attendance_id=att.id,
            schedule_id=att.schedule_id,
            schedule_date=schedule.schedule_date if schedule else date.today(),
            class_plan_name=class_plan.name if class_plan else "",
            status=att.status,
            leave_reason=att.leave_reason,
            deduct_hours=att.deduct_hours,
        ))

    # 按日期排序
    recent_attendance.sort(key=lambda x: x.schedule_date, reverse=True)

    # 2. 查询课时消耗记录
    lesson_query = (
        select(LessonRecord)
        .options(
            selectinload(LessonRecord.enrollment).selectinload(Enrollment.class_plan).selectinload(ClassPlan.course),
            selectinload(LessonRecord.enrollment).selectinload(Enrollment.class_plan).selectinload(ClassPlan.teacher),
        )
        .where(LessonRecord.enrollment_id.in_(enrollment_ids))
    )

    # 应用时间过滤
    if start_date:
        lesson_query = lesson_query.where(LessonRecord.record_date >= start_date)
    if end_date:
        lesson_query = lesson_query.where(LessonRecord.record_date <= end_date)

    lesson_query = lesson_query.order_by(LessonRecord.record_date.desc())

    lesson_result = await db.execute(lesson_query)
    lessons = lesson_result.scalars().all()

    lesson_records = []
    for lr in lessons:
        class_plan = lr.enrollment.class_plan if lr.enrollment else None
        course = class_plan.course if class_plan else None
        teacher = class_plan.teacher if class_plan else None

        lesson_records.append(StudentLessonRecord(
            record_id=lr.id,
            record_date=lr.record_date,
            hours=lr.hours,
            class_plan_name=class_plan.name if class_plan else "",
            course_name=course.name if course else "",
            teacher_name=teacher.name if teacher else None,
            type=lr.type,
            notes=lr.notes,
        ))

    response = StudentDashboardRecords(
        attendance_summary=attendance_summary,
        recent_attendance=recent_attendance,
        lesson_records=lesson_records,
        consumption_trend=[],  # 可以后续扩展
    )

    return success_response(response.model_dump())
