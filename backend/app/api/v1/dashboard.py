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
    DistributionItem,
    TrendDataPoint as DashboardTrendDataPoint,
    StudentDashboardOverview,
    StudentDashboardCourses,
    StudentDashboardRecords,
    StudentScheduleItem,
    StudentEnrollmentItem,
    StudentAttendanceRecord,
    StudentLessonRecord,
    TeacherDashboardOverview,
    TeacherDashboardClasses,
    TeacherDashboardIncome,
    TeacherScheduleItem,
    TeacherClassItem,
    TeacherStudentAttendance,
)
from app.models.campus import Campus

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


# ========== 教师仪表盘端点 ==========

async def _get_teacher_for_user(db: DBSession, user_id: int) -> Teacher:
    """
    根据用户ID获取关联的教师记录。
    教师通过 Teacher.user_id 关联到用户账号。
    """
    result = await db.execute(
        select(Teacher).where(Teacher.user_id == user_id)
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise NotFoundException("未找到关联的教师记录")
    return teacher


def _require_teacher_role(current_user, scope: CampusScopedQuery):
    """
    检查当前用户是否是教师角色。
    如果不是教师角色，抛出 403 错误。
    """
    role_code = scope.get_token_role_code(current_user)
    if role_code != "teacher":
        raise ForbiddenException("此接口仅供教师访问")


@router.get("/teacher", summary="教师仪表盘概览")
async def get_teacher_dashboard_overview(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    获取教师仪表盘概览数据。
    包含：
    - KPI卡片：今日课程数、本周课程数、本月课时数、在教班级数
    - 今日排课列表
    - 近期排课列表（未来7天）
    """
    scope = CampusScopedQuery()
    _require_teacher_role(current_user, scope)

    # 获取教师记录
    teacher = await _get_teacher_for_user(db, current_user.id)

    today = date.today()
    next_week = today + timedelta(days=7)
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())

    # 1. 查询教师的活跃班级
    class_plan_result = await db.execute(
        select(ClassPlan)
        .where(
            and_(
                ClassPlan.teacher_id == teacher.id,
                ClassPlan.is_active == True,
                ClassPlan.status.in_(["ongoing", "not_started"]),
            )
        )
    )
    active_class_plans = class_plan_result.scalars().all()

    # 2. 查询今日排课
    today_schedule_result = await db.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.class_plan).selectinload(ClassPlan.course),
            selectinload(Schedule.classroom),
        )
        .where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.schedule_date == today,
                Schedule.status != "cancelled",
            )
        )
        .order_by(Schedule.start_time)
    )
    today_schedules_raw = today_schedule_result.scalars().all()

    # 3. 查询本周课程数
    week_schedule_count = (await db.execute(
        select(func.count())
        .select_from(Schedule)
        .where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.schedule_date >= week_start,
                Schedule.schedule_date <= week_start + timedelta(days=6),
                Schedule.status != "cancelled",
            )
        )
    )).scalar() or 0

    # 4. 查询本月已完成课时数
    month_hours_result = await db.execute(
        select(func.sum(Schedule.lesson_hours))
        .where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.schedule_date >= month_start,
                Schedule.schedule_date <= today,
                Schedule.status == "completed",
            )
        )
    )
    month_lesson_hours = float(month_hours_result.scalar() or 0)

    # 5. 查询近期排课（未来7天，包括今日）
    upcoming_result = await db.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.class_plan).selectinload(ClassPlan.course),
            selectinload(Schedule.classroom),
        )
        .where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.schedule_date >= today,
                Schedule.schedule_date <= next_week,
                Schedule.status != "cancelled",
            )
        )
        .order_by(Schedule.schedule_date, Schedule.start_time)
    )
    upcoming_schedules_raw = upcoming_result.scalars().all()

    # 6. 获取每个排课的学生人数
    schedule_ids = [s.id for s in upcoming_schedules_raw]
    student_counts = {}
    if schedule_ids:
        # 通过 class_plan 获取报名人数
        class_plan_ids = list(set(s.class_plan_id for s in upcoming_schedules_raw))
        enrollment_counts = await db.execute(
            select(
                Enrollment.class_plan_id,
                func.count(Enrollment.id).label("count")
            )
            .where(
                and_(
                    Enrollment.class_plan_id.in_(class_plan_ids),
                    Enrollment.status == "active",
                )
            )
            .group_by(Enrollment.class_plan_id)
        )
        class_plan_student_counts = {row.class_plan_id: row.count for row in enrollment_counts}
        for s in upcoming_schedules_raw:
            student_counts[s.id] = class_plan_student_counts.get(s.class_plan_id, 0)

    # 构建排课列表
    def _build_teacher_schedule_item(schedule: Schedule) -> TeacherScheduleItem:
        class_plan = schedule.class_plan
        course = class_plan.course if class_plan else None
        return TeacherScheduleItem(
            schedule_id=schedule.id,
            schedule_date=schedule.schedule_date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            lesson_hours=float(schedule.lesson_hours or 0),
            class_plan_id=schedule.class_plan_id,
            class_plan_name=class_plan.name if class_plan else "",
            course_name=course.name if course else "",
            classroom_name=schedule.classroom.name if schedule.classroom else None,
            campus_name=None,  # 可以后续加载
            student_count=student_counts.get(schedule.id, 0),
            status=schedule.status,
        )

    today_schedules = [_build_teacher_schedule_item(s) for s in today_schedules_raw]
    upcoming_schedules = [_build_teacher_schedule_item(s) for s in upcoming_schedules_raw]

    # 构建响应
    response = TeacherDashboardOverview(
        today_class_count=KpiCard(
            label="今日课程",
            value=len(today_schedules),
            unit="节",
        ),
        week_class_count=KpiCard(
            label="本周课程",
            value=week_schedule_count,
            unit="节",
        ),
        month_lesson_hours=KpiCard(
            label="本月课时",
            value=month_lesson_hours,
            unit="课时",
        ),
        active_class_count=KpiCard(
            label="在教班级",
            value=len(active_class_plans),
            unit="个",
        ),
        upcoming_schedules=upcoming_schedules,
        today_schedules=today_schedules,
    )

    return success_response(response.model_dump())


@router.get("/teacher/classes", summary="教师教学情况")
async def get_teacher_classes(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    获取教师的教学情况。
    包含：
    - 授课班级列表（包括学生人数、排课完成情况）
    - 学生出勤统计
    - 班级学生分布图
    """
    scope = CampusScopedQuery()
    _require_teacher_role(current_user, scope)

    # 获取教师记录
    teacher = await _get_teacher_for_user(db, current_user.id)

    # 1. 查询教师的所有班级
    class_plan_result = await db.execute(
        select(ClassPlan)
        .options(
            selectinload(ClassPlan.course),
            selectinload(ClassPlan.campus),
        )
        .where(
            and_(
                ClassPlan.teacher_id == teacher.id,
                ClassPlan.is_active == True,
            )
        )
    )
    class_plans = class_plan_result.scalars().all()
    class_plan_ids = [cp.id for cp in class_plans]

    if not class_plan_ids:
        # 没有班级，返回空数据
        return success_response(TeacherDashboardClasses(
            classes=[],
            student_attendance=[],
            students_by_class=[],
        ).model_dump())

    # 2. 获取每个班级的报名人数
    enrollment_counts_result = await db.execute(
        select(
            Enrollment.class_plan_id,
            func.count(Enrollment.id).label("count")
        )
        .where(
            and_(
                Enrollment.class_plan_id.in_(class_plan_ids),
                Enrollment.status == "active",
            )
        )
        .group_by(Enrollment.class_plan_id)
    )
    enrollment_counts = {row.class_plan_id: row.count for row in enrollment_counts_result}

    # 3. 获取每个班级的排课统计
    schedule_stats_result = await db.execute(
        select(
            Schedule.class_plan_id,
            func.count(Schedule.id).label("total"),
            func.sum(func.cast(Schedule.status == "completed", Integer)).label("completed")
        )
        .where(
            and_(
                Schedule.class_plan_id.in_(class_plan_ids),
                Schedule.status != "cancelled",
            )
        )
        .group_by(Schedule.class_plan_id)
    )
    schedule_stats = {
        row.class_plan_id: (row.total, row.completed or 0)
        for row in schedule_stats_result
    }

    # 构建班级列表
    class_items = []
    students_by_class = []
    for cp in class_plans:
        student_count = enrollment_counts.get(cp.id, 0)
        total_schedules, completed_schedules = schedule_stats.get(cp.id, (0, 0))

        class_items.append(TeacherClassItem(
            class_plan_id=cp.id,
            class_plan_name=cp.name,
            course_name=cp.course.name if cp.course else "",
            campus_name=cp.campus.name if cp.campus else None,
            student_count=student_count,
            total_schedules=total_schedules,
            completed_schedules=completed_schedules,
            remaining_schedules=total_schedules - completed_schedules,
            status=cp.status,
        ))

        # 班级学生分布
        if student_count > 0:
            students_by_class.append(DistributionItem(
                name=cp.name,
                value=float(student_count),
            ))

    # 4. 获取学生出勤统计
    # 首先获取这些班级的所有报名
    enrollments_result = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.student))
        .where(
            and_(
                Enrollment.class_plan_id.in_(class_plan_ids),
                Enrollment.status == "active",
            )
        )
    )
    enrollments = enrollments_result.scalars().all()
    enrollment_ids = [e.id for e in enrollments]

    student_attendance_list = []
    if enrollment_ids:
        # 获取出勤统计
        attendance_stats_result = await db.execute(
            select(
                StudentAttendance.enrollment_id,
                func.count(StudentAttendance.id).label("total"),
                func.sum(func.cast(StudentAttendance.status == "normal", Integer)).label("normal"),
                func.sum(func.cast(StudentAttendance.status == "leave", Integer)).label("leave"),
                func.sum(func.cast(StudentAttendance.status == "absent", Integer)).label("absent")
            )
            .where(StudentAttendance.enrollment_id.in_(enrollment_ids))
            .group_by(StudentAttendance.enrollment_id)
        )
        attendance_stats = {
            row.enrollment_id: (row.total, row.normal or 0, row.leave or 0, row.absent or 0)
            for row in attendance_stats_result
        }

        # 构建学生出勤列表
        for e in enrollments:
            total, normal, leave, absent = attendance_stats.get(e.id, (0, 0, 0, 0))
            attendance_rate = round((normal / total * 100) if total > 0 else 0, 1)

            student_attendance_list.append(TeacherStudentAttendance(
                student_id=e.student.id if e.student else 0,
                student_name=e.student.name if e.student else "",
                total_count=total,
                normal_count=normal,
                leave_count=leave,
                absent_count=absent,
                attendance_rate=attendance_rate,
            ))

    response = TeacherDashboardClasses(
        classes=class_items,
        student_attendance=student_attendance_list,
        students_by_class=students_by_class,
    )

    return success_response(response.model_dump())


@router.get("/teacher/income", summary="教师课时收入")
async def get_teacher_income(
    current_user: CurrentUser,
    db: DBSession,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    """
    获取教师的课时收入统计。
    包含：
    - KPI：本月预估收入、本月已授课时、课时单价
    - 收入趋势（按月）
    - 课时趋势（按月）
    - 课时分布（按班级）
    """
    scope = CampusScopedQuery()
    _require_teacher_role(current_user, scope)

    # 获取教师记录
    teacher = await _get_teacher_for_user(db, current_user.id)

    today = date.today()
    month_start = today.replace(day=1)
    hourly_rate = float(teacher.hourly_rate or 0)

    # 如果有时间过滤，使用过滤时间；否则使用本月
    query_start = start_date if start_date else month_start
    query_end = end_date if end_date else today

    # 1. 查询已完成的课时数（在查询时间范围内）
    month_hours_result = await db.execute(
        select(func.sum(Schedule.lesson_hours))
        .where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.schedule_date >= query_start,
                Schedule.schedule_date <= query_end,
                Schedule.status == "completed",
            )
        )
    )
    month_hours = float(month_hours_result.scalar() or 0)
    month_income = month_hours * hourly_rate

    # 2. 查询课时分布（按班级）
    hours_by_class_result = await db.execute(
        select(
            ClassPlan.name,
            func.sum(Schedule.lesson_hours).label("hours")
        )
        .join(ClassPlan, ClassPlan.id == Schedule.class_plan_id)
        .where(
            and_(
                Schedule.teacher_id == teacher.id,
                Schedule.schedule_date >= query_start,
                Schedule.schedule_date <= query_end,
                Schedule.status == "completed",
            )
        )
        .group_by(ClassPlan.id, ClassPlan.name)
    )
    hours_by_class = [
        DistributionItem(name=row.name, value=float(row.hours or 0))
        for row in hours_by_class_result
    ]

    # 3. 计算趋势数据（最近6个月）
    income_trend = []
    hours_trend = []

    # 获取最近6个月的数据
    for i in range(5, -1, -1):
        # 计算月份
        month_offset = today.month - i
        year_offset = today.year
        while month_offset <= 0:
            month_offset += 12
            year_offset -= 1
        while month_offset > 12:
            month_offset -= 12
            year_offset += 1

        m_start = date(year_offset, month_offset, 1)
        # 计算月末
        if month_offset == 12:
            m_end = date(year_offset + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(year_offset, month_offset + 1, 1) - timedelta(days=1)

        # 查询这个月的课时
        m_hours_result = await db.execute(
            select(func.sum(Schedule.lesson_hours))
            .where(
                and_(
                    Schedule.teacher_id == teacher.id,
                    Schedule.schedule_date >= m_start,
                    Schedule.schedule_date <= m_end,
                    Schedule.status == "completed",
                )
            )
        )
        m_hours = float(m_hours_result.scalar() or 0)
        m_income = m_hours * hourly_rate

        date_label = m_start.strftime("%Y-%m")
        income_trend.append(DashboardTrendDataPoint(
            date=date_label,
            value=m_income,
            label=f"{m_start.month}月",
        ))
        hours_trend.append(DashboardTrendDataPoint(
            date=date_label,
            value=m_hours,
            label=f"{m_start.month}月",
        ))

    response = TeacherDashboardIncome(
        month_income=KpiCard(
            label="本月预估收入",
            value=month_income,
            unit="元",
            is_time_filtered=bool(start_date or end_date),
        ),
        month_hours=KpiCard(
            label="本月已授课时",
            value=month_hours,
            unit="课时",
            is_time_filtered=bool(start_date or end_date),
        ),
        hourly_rate=KpiCard(
            label="课时单价",
            value=hourly_rate,
            unit="元/课时",
        ),
        income_trend=income_trend,
        hours_trend=hours_trend,
        hours_by_class=hours_by_class,
    )

    return success_response(response.model_dump())


# ========== 管理员仪表盘端点 ==========

def _require_admin_role(current_user, scope: CampusScopedQuery):
    """
    检查当前用户是否是管理员角色（超管或校区管理员）。
    如果不是管理员角色，抛出 403 错误。
    """
    role_code = scope.get_token_role_code(current_user)
    if role_code not in ("super_admin", "campus_admin"):
        raise ForbiddenException("此接口仅供管理员访问")


class AdminDashboardResponse(BaseModel):
    """管理员仪表盘响应（灵活格式）"""
    kpi_cards: List[dict]
    enrollment_trend: List[dict]
    revenue_trend: Optional[List[dict]] = None
    campus_comparison: Optional[List[dict]] = None


@router.get("/admin", summary="管理员仪表盘概览")
async def get_admin_dashboard_overview(
    current_user: CurrentUser,
    db: DBSession,
    campus_id: Optional[int] = Query(None, description="校区ID（超管可选）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    """
    获取管理员仪表盘概览数据。
    包含：
    - KPI卡片：学生总数、教师总数、进行中班级数、本月收入
    - 报名趋势（近7天）
    - 收入趋势（近7天）
    - 校区对比（仅超管不选校区时返回）

    权限：
    - 超管可以选择校区或查看全部
    - 校区管理员只能看自己校区
    """
    scope = CampusScopedQuery()
    _require_admin_role(current_user, scope)

    role_code = scope.get_token_role_code(current_user)
    is_super_admin = role_code == "super_admin"
    token_campus_id = scope.get_campus_filter(current_user)

    # 确定要查询的校区范围
    filter_campus_id = None
    show_campus_comparison = False

    if is_super_admin:
        # 超管可以选择校区
        if campus_id:
            filter_campus_id = campus_id
        elif token_campus_id:
            filter_campus_id = token_campus_id
        else:
            # 超管未选校区，显示全部数据和校区对比
            show_campus_comparison = True
    else:
        # 校区管理员只能看自己校区
        filter_campus_id = token_campus_id

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)

    # 如果有时间过滤，使用过滤时间
    query_start = start_date if start_date else week_ago
    query_end = end_date if end_date else today

    # 1. 查询学生总数
    student_query = select(func.count()).select_from(Student).where(Student.status == "active")
    if filter_campus_id:
        student_query = student_query.where(Student.campus_id == filter_campus_id)
    total_students = (await db.execute(student_query)).scalar() or 0

    # 2. 查询教师总数（教师无校区限制，但可以统计有排课的教师）
    teacher_query = select(func.count()).select_from(Teacher).where(Teacher.is_active == True)
    total_teachers = (await db.execute(teacher_query)).scalar() or 0

    # 3. 查询进行中班级数
    class_plan_query = (
        select(func.count())
        .select_from(ClassPlan)
        .where(
            and_(
                ClassPlan.is_active == True,
                ClassPlan.status == "ongoing",
            )
        )
    )
    if filter_campus_id:
        class_plan_query = class_plan_query.where(ClassPlan.campus_id == filter_campus_id)
    active_classes = (await db.execute(class_plan_query)).scalar() or 0

    # 4. 查询本月收入（报名的paid_amount）
    revenue_query = (
        select(func.sum(Enrollment.paid_amount))
        .where(
            and_(
                Enrollment.created_time >= datetime.combine(month_start, datetime.min.time()),
                Enrollment.status == "active",
            )
        )
    )
    if filter_campus_id:
        revenue_query = revenue_query.where(Enrollment.campus_id == filter_campus_id)
    month_revenue = float((await db.execute(revenue_query)).scalar() or 0)

    # 5. 构建KPI卡片
    kpi_cards = [
        KpiCard(
            label="学生总数",
            value=total_students,
            unit="人",
        ).model_dump(),
        KpiCard(
            label="教师总数",
            value=total_teachers,
            unit="人",
        ).model_dump(),
        KpiCard(
            label="进行中班级",
            value=active_classes,
            unit="个",
        ).model_dump(),
        KpiCard(
            label="本月收入",
            value=month_revenue,
            unit="元",
            is_time_filtered=bool(start_date or end_date),
        ).model_dump(),
    ]

    # 6. 查询报名趋势（近7天）
    # 使用 func.date() 以兼容 SQLite
    enrollment_trend_query = (
        select(
            func.date(Enrollment.created_time).label("enroll_date"),
            func.count(Enrollment.id).label("count"),
        )
        .where(
            and_(
                Enrollment.created_time >= datetime.combine(query_start, datetime.min.time()),
                Enrollment.created_time <= datetime.combine(query_end, datetime.max.time()),
            )
        )
        .group_by(func.date(Enrollment.created_time))
        .order_by(func.date(Enrollment.created_time))
    )
    if filter_campus_id:
        enrollment_trend_query = enrollment_trend_query.where(Enrollment.campus_id == filter_campus_id)

    enrollment_trend_result = await db.execute(enrollment_trend_query)
    # enroll_date 可能是字符串或 date 对象，需要统一处理
    enrollment_data = {}
    for row in enrollment_trend_result:
        d = row.enroll_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        enrollment_data[d] = row.count

    # 补齐所有日期
    enrollment_trend = []
    current = query_start
    while current <= query_end:
        date_str = current.strftime("%Y-%m-%d")
        count = enrollment_data.get(current, 0)
        enrollment_trend.append(DashboardTrendDataPoint(
            date=date_str,
            value=float(count),
            label=current.strftime("%m-%d"),
        ).model_dump())
        current += timedelta(days=1)

    # 7. 查询收入趋势（近7天）
    # 使用 func.date() 以兼容 SQLite
    revenue_trend_query = (
        select(
            func.date(Enrollment.created_time).label("enroll_date"),
            func.sum(Enrollment.paid_amount).label("amount"),
        )
        .where(
            and_(
                Enrollment.created_time >= datetime.combine(query_start, datetime.min.time()),
                Enrollment.created_time <= datetime.combine(query_end, datetime.max.time()),
                Enrollment.status == "active",
            )
        )
        .group_by(func.date(Enrollment.created_time))
        .order_by(func.date(Enrollment.created_time))
    )
    if filter_campus_id:
        revenue_trend_query = revenue_trend_query.where(Enrollment.campus_id == filter_campus_id)

    revenue_trend_result = await db.execute(revenue_trend_query)
    # enroll_date 可能是字符串或 date 对象，需要统一处理
    revenue_data = {}
    for row in revenue_trend_result:
        d = row.enroll_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        revenue_data[d] = float(row.amount or 0)

    # 补齐所有日期
    revenue_trend = []
    current = query_start
    while current <= query_end:
        date_str = current.strftime("%Y-%m-%d")
        amount = revenue_data.get(current, 0)
        revenue_trend.append(DashboardTrendDataPoint(
            date=date_str,
            value=amount,
            label=current.strftime("%m-%d"),
        ).model_dump())
        current += timedelta(days=1)

    # 8. 校区对比（仅超管不选校区时）
    campus_comparison = None
    if show_campus_comparison:
        # 获取所有校区
        campuses_result = await db.execute(
            select(Campus).where(Campus.is_active == True)
        )
        campuses = campuses_result.scalars().all()

        campus_comparison = []
        for campus in campuses:
            # 查询每个校区的学生数
            c_students = (await db.execute(
                select(func.count())
                .select_from(Student)
                .where(
                    and_(
                        Student.campus_id == campus.id,
                        Student.status == "active",
                    )
                )
            )).scalar() or 0

            # 查询每个校区的班级数
            c_classes = (await db.execute(
                select(func.count())
                .select_from(ClassPlan)
                .where(
                    and_(
                        ClassPlan.campus_id == campus.id,
                        ClassPlan.is_active == True,
                        ClassPlan.status == "ongoing",
                    )
                )
            )).scalar() or 0

            # 查询每个校区的本月收入
            c_revenue = float((await db.execute(
                select(func.sum(Enrollment.paid_amount))
                .where(
                    and_(
                        Enrollment.campus_id == campus.id,
                        Enrollment.created_time >= datetime.combine(month_start, datetime.min.time()),
                        Enrollment.status == "active",
                    )
                )
            )).scalar() or 0)

            campus_comparison.append({
                "campus_id": campus.id,
                "campus_name": campus.name,
                "students": c_students,
                "active_classes": c_classes,
                "month_revenue": c_revenue,
            })

    # 构建响应
    response_data = {
        "kpi_cards": kpi_cards,
        "enrollment_trend": enrollment_trend,
        "revenue_trend": revenue_trend,
    }

    if campus_comparison is not None:
        response_data["campus_comparison"] = campus_comparison

    return success_response(response_data)
