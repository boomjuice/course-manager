"""
LessonRecord service - 课时消耗记录服务
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lesson_record import LessonRecord
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule
from app.models.student import Student
from app.schemas.lesson_record import LessonRecordCreate, LessonRecordResponse


class LessonRecordService:
    """课时消耗记录服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_schedule(
        self,
        schedule: Schedule,
        created_by: str
    ) -> List[LessonRecord]:
        """
        从排课创建课时消耗记录
        当排课状态改为"completed"时调用此方法
        为该班级所有在读学生创建消耗记录
        """
        # 获取该班级所有在读的报名记录
        result = await self.db.execute(
            select(Enrollment)
            .options(selectinload(Enrollment.student))
            .where(
                Enrollment.class_plan_id == schedule.class_plan_id,
                Enrollment.status == "active"
            )
        )
        enrollments = list(result.scalars().all())

        created_records: List[LessonRecord] = []
        hours = Decimal(str(schedule.lesson_hours))

        for enrollment in enrollments:
            # 创建消耗记录
            record = LessonRecord(
                enrollment_id=enrollment.id,
                schedule_id=schedule.id,
                record_date=schedule.schedule_date,
                hours=hours,
                type="schedule",
                notes=f"排课消耗: {schedule.title or '课程'}",
                created_by=created_by,
            )
            self.db.add(record)
            created_records.append(record)

            # 更新报名记录的已用课时
            enrollment.used_hours = Decimal(str(enrollment.used_hours or 0)) + hours

            # 更新学生的剩余课时
            if enrollment.student:
                enrollment.student.remaining_hours = max(
                    Decimal("0"),
                    Decimal(str(enrollment.student.remaining_hours or 0)) - hours
                )

        await self.db.flush()
        return created_records

    async def reverse_from_schedule(
        self,
        schedule: Schedule,
        updated_by: str
    ) -> int:
        """
        撤销排课的课时消耗记录
        当排课状态从"completed"改回其他状态时调用
        """
        # 查找该排课的所有消耗记录
        result = await self.db.execute(
            select(LessonRecord)
            .options(selectinload(LessonRecord.enrollment).selectinload(Enrollment.student))
            .where(LessonRecord.schedule_id == schedule.id)
        )
        records = list(result.scalars().all())

        for record in records:
            enrollment = record.enrollment
            if enrollment:
                # 恢复报名记录的已用课时
                enrollment.used_hours = max(
                    Decimal("0"),
                    Decimal(str(enrollment.used_hours or 0)) - record.hours
                )

                # 恢复学生的剩余课时
                if enrollment.student:
                    enrollment.student.remaining_hours = (
                        Decimal(str(enrollment.student.remaining_hours or 0)) + record.hours
                    )

            # 删除消耗记录
            await self.db.delete(record)

        await self.db.flush()
        return len(records)

    async def get_by_enrollment(
        self,
        enrollment_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[LessonRecordResponse], int]:
        """获取某个报名记录的课时消耗历史"""
        query = (
            select(LessonRecord)
            .options(
                selectinload(LessonRecord.enrollment).selectinload(Enrollment.student),
                selectinload(LessonRecord.enrollment).selectinload(Enrollment.class_plan),
                selectinload(LessonRecord.schedule).selectinload(Schedule.teacher),
            )
            .where(LessonRecord.enrollment_id == enrollment_id)
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            query
            .order_by(LessonRecord.record_date.desc(), LessonRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        records = list(result.scalars().all())

        # 转换为响应格式
        items = []
        for r in records:
            item = LessonRecordResponse(
                id=r.id,
                enrollment_id=r.enrollment_id,
                schedule_id=r.schedule_id,
                record_date=r.record_date,
                hours=r.hours,
                type=r.type,
                notes=r.notes,
                created_time=r.created_time,
                student_name=r.enrollment.student.name if r.enrollment and r.enrollment.student else None,
                class_plan_name=r.enrollment.class_plan.name if r.enrollment and r.enrollment.class_plan else None,
                teacher_name=r.schedule.teacher.name if r.schedule and r.schedule.teacher else None,
                schedule_date=r.schedule.schedule_date if r.schedule else None,
            )
            items.append(item)

        return items, total

    async def get_by_student(
        self,
        student_id: int,
        page: int = 1,
        page_size: int = 20,
        class_plan_id: Optional[int] = None,
    ) -> Tuple[List[LessonRecordResponse], int]:
        """获取某个学生的所有课时消耗历史"""
        query = (
            select(LessonRecord)
            .join(Enrollment)
            .options(
                selectinload(LessonRecord.enrollment).selectinload(Enrollment.student),
                selectinload(LessonRecord.enrollment).selectinload(Enrollment.class_plan),
                selectinload(LessonRecord.schedule).selectinload(Schedule.teacher),
            )
            .where(Enrollment.student_id == student_id)
        )

        if class_plan_id:
            query = query.where(Enrollment.class_plan_id == class_plan_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            query
            .order_by(LessonRecord.record_date.desc(), LessonRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        records = list(result.scalars().all())

        # 转换为响应格式
        items = []
        for r in records:
            item = LessonRecordResponse(
                id=r.id,
                enrollment_id=r.enrollment_id,
                schedule_id=r.schedule_id,
                record_date=r.record_date,
                hours=r.hours,
                type=r.type,
                notes=r.notes,
                created_time=r.created_time,
                student_name=r.enrollment.student.name if r.enrollment and r.enrollment.student else None,
                class_plan_name=r.enrollment.class_plan.name if r.enrollment and r.enrollment.class_plan else None,
                teacher_name=r.schedule.teacher.name if r.schedule and r.schedule.teacher else None,
                schedule_date=r.schedule.schedule_date if r.schedule else None,
            )
            items.append(item)

        return items, total
