"""
Dashboard API endpoints - statistics and overview data.
"""
from typing import Optional, List
from datetime import datetime, timedelta, date
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date

from app.api.deps import CurrentUser, DBSession
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class_plan import ClassPlan
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.schemas.common import success_response

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
