"""
Student Attendance service.
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student_attendance import StudentAttendance
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule
from app.models.student import Student
from app.models.class_plan import ClassPlan
from app.schemas.student_attendance import (
    StudentAttendanceCreate,
    StudentAttendanceUpdate,
    AttendanceMarkRequest,
)
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException


class StudentAttendanceService:
    """Student attendance service - 学生出勤管理"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, attendance_id: int) -> StudentAttendance:
        """Get attendance by ID."""
        result = await self.db.execute(
            select(StudentAttendance).where(StudentAttendance.id == attendance_id)
        )
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise NotFoundException(f"出勤记录不存在: {attendance_id}")
        return attendance

    async def get_by_enrollment_and_schedule(
        self, enrollment_id: int, schedule_id: int
    ) -> Optional[StudentAttendance]:
        """Get attendance by enrollment and schedule."""
        result = await self.db.execute(
            select(StudentAttendance).where(
                StudentAttendance.enrollment_id == enrollment_id,
                StudentAttendance.schedule_id == schedule_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_student_attendance_list(
        self,
        student_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """Get student's attendance records with detailed info."""
        # 先获取学生的所有报名
        enrollment_result = await self.db.execute(
            select(Enrollment.id).where(Enrollment.student_id == student_id)
        )
        enrollment_ids = [row[0] for row in enrollment_result.fetchall()]

        if not enrollment_ids:
            return [], 0

        # 查询出勤记录
        query = (
            select(StudentAttendance)
            .options(
                selectinload(StudentAttendance.enrollment),
                selectinload(StudentAttendance.schedule),
            )
            .where(StudentAttendance.enrollment_id.in_(enrollment_ids))
        )

        if status:
            query = query.where(StudentAttendance.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Paginate
        query = (
            query.order_by(StudentAttendance.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        attendances = result.scalars().all()

        # 构造详细响应
        items = []
        for att in attendances:
            schedule = att.schedule
            class_plan_name = None
            if schedule and schedule.class_plan_id:
                cp_result = await self.db.execute(
                    select(ClassPlan.name).where(ClassPlan.id == schedule.class_plan_id)
                )
                class_plan_name = cp_result.scalar_one_or_none()

            items.append({
                "id": att.id,
                "enrollment_id": att.enrollment_id,
                "schedule_id": att.schedule_id,
                "status": att.status,
                "leave_reason": att.leave_reason,
                "apply_time": att.apply_time,
                "deduct_hours": att.deduct_hours,
                "notes": att.notes,
                "schedule_date": str(schedule.schedule_date) if schedule else None,
                "class_plan_name": class_plan_name,
            })

        return items, total_count

    async def get_schedule_attendance_list(
        self, schedule_id: int
    ) -> List[dict]:
        """Get all students' attendance for a schedule."""
        # 获取schedule
        schedule_result = await self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()
        if not schedule:
            raise NotFoundException(f"排课不存在: {schedule_id}")

        # 获取该班级的所有报名学生
        enrollment_result = await self.db.execute(
            select(Enrollment)
            .options(selectinload(Enrollment.student))
            .where(
                Enrollment.class_plan_id == schedule.class_plan_id,
                Enrollment.status == "active",
            )
        )
        enrollments = list(enrollment_result.scalars().all())

        # 获取已有的出勤记录
        att_result = await self.db.execute(
            select(StudentAttendance).where(
                StudentAttendance.schedule_id == schedule_id
            )
        )
        att_map = {att.enrollment_id: att for att in att_result.scalars().all()}

        items = []
        for enroll in enrollments:
            att = att_map.get(enroll.id)
            items.append({
                "enrollment_id": enroll.id,
                "student_id": enroll.student_id,
                "student_name": enroll.student.name if enroll.student else None,
                "status": att.status if att else "normal",
                "leave_reason": att.leave_reason if att else None,
                "apply_time": att.apply_time if att else None,
                "attendance_id": att.id if att else None,
            })

        return items

    async def apply_leave(
        self,
        student_id: int,
        schedule_id: int,
        leave_reason: str,
        applied_by: str,
    ) -> StudentAttendance:
        """Student applies for leave - 学生申请请假"""
        # 获取schedule
        schedule_result = await self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()
        if not schedule:
            raise NotFoundException(f"排课不存在: {schedule_id}")

        # 获取学生在该班级的报名
        enrollment_result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.class_plan_id == schedule.class_plan_id,
                Enrollment.status == "active",
            )
        )
        enrollment = enrollment_result.scalar_one_or_none()
        if not enrollment:
            raise BadRequestException("学生未报名该班级")

        # 检查是否已有出勤记录
        existing = await self.get_by_enrollment_and_schedule(enrollment.id, schedule_id)
        if existing:
            # 更新为请假
            existing.status = "leave"
            existing.leave_reason = leave_reason
            existing.apply_time = datetime.now()
            existing.updated_by = applied_by
            await self.db.flush()
            return existing

        # 创建新的出勤记录
        attendance = StudentAttendance(
            enrollment_id=enrollment.id,
            schedule_id=schedule_id,
            status="leave",
            leave_reason=leave_reason,
            apply_time=datetime.now(),
            deduct_hours=False,  # 请假默认不扣课时
            created_by=applied_by,
        )
        self.db.add(attendance)
        await self.db.flush()
        return attendance

    async def mark_attendance(
        self,
        data: AttendanceMarkRequest,
        marked_by: str,
    ) -> StudentAttendance:
        """Admin marks student attendance - 管理员标记出勤"""
        # 验证enrollment
        enrollment_result = await self.db.execute(
            select(Enrollment).where(Enrollment.id == data.enrollment_id)
        )
        enrollment = enrollment_result.scalar_one_or_none()
        if not enrollment:
            raise NotFoundException(f"报名记录不存在: {data.enrollment_id}")

        # 验证schedule
        schedule_result = await self.db.execute(
            select(Schedule).where(Schedule.id == data.schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()
        if not schedule:
            raise NotFoundException(f"排课不存在: {data.schedule_id}")

        # 检查是否已有出勤记录
        existing = await self.get_by_enrollment_and_schedule(data.enrollment_id, data.schedule_id)
        if existing:
            # 更新
            existing.status = data.status
            existing.leave_reason = data.leave_reason
            existing.deduct_hours = data.deduct_hours
            existing.notes = data.notes
            existing.updated_by = marked_by
            await self.db.flush()
            return existing

        # 创建新记录
        attendance = StudentAttendance(
            enrollment_id=data.enrollment_id,
            schedule_id=data.schedule_id,
            status=data.status,
            leave_reason=data.leave_reason,
            apply_time=datetime.now() if data.status == "leave" else None,
            deduct_hours=data.deduct_hours,
            notes=data.notes,
            created_by=marked_by,
        )
        self.db.add(attendance)
        await self.db.flush()
        return attendance

    async def get_upcoming_schedules_for_student(
        self, student_id: int, days: int = 7
    ) -> List[dict]:
        """Get upcoming schedules for a student (for leave application)."""
        from datetime import date, timedelta

        today = date.today()
        end_date = today + timedelta(days=days)

        # 获取学生的所有活跃报名
        enrollment_result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.status == "active",
            )
        )
        enrollments = list(enrollment_result.scalars().all())

        if not enrollments:
            return []

        class_plan_ids = [e.class_plan_id for e in enrollments]
        enrollment_map = {e.class_plan_id: e.id for e in enrollments}

        # 获取未来的排课
        schedule_result = await self.db.execute(
            select(Schedule)
            .where(
                Schedule.class_plan_id.in_(class_plan_ids),
                Schedule.schedule_date >= today,
                Schedule.schedule_date <= end_date,
                Schedule.status == "scheduled",
            )
            .order_by(Schedule.schedule_date, Schedule.start_time)
        )
        schedules = list(schedule_result.scalars().all())

        # 获取班级名称
        class_plan_result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id.in_(class_plan_ids))
        )
        class_plan_map = {cp.id: cp.name for cp in class_plan_result.scalars().all()}

        # 获取已有的出勤记录（请假状态）
        schedule_ids = [s.id for s in schedules]
        enrollment_ids = [e.id for e in enrollments]
        if schedule_ids:
            att_result = await self.db.execute(
                select(StudentAttendance).where(
                    StudentAttendance.schedule_id.in_(schedule_ids),
                    StudentAttendance.enrollment_id.in_(enrollment_ids),
                )
            )
            att_map = {(att.enrollment_id, att.schedule_id): att for att in att_result.scalars().all()}
        else:
            att_map = {}

        items = []
        for s in schedules:
            enrollment_id = enrollment_map.get(s.class_plan_id)
            att = att_map.get((enrollment_id, s.id))
            items.append({
                "schedule_id": s.id,
                "enrollment_id": enrollment_id,
                "schedule_date": str(s.schedule_date),
                "start_time": str(s.start_time),
                "end_time": str(s.end_time),
                "class_plan_name": class_plan_map.get(s.class_plan_id),
                "title": s.title,
                "attendance_status": att.status if att else None,
                "leave_reason": att.leave_reason if att else None,
            })

        return items
