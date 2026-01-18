"""
Enrollment service with campus scope support.
报名服务层，支持校区数据隔离。
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.class_plan import ClassPlan
from app.models.schedule import Schedule
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse
from app.core.exceptions import NotFoundException, ForbiddenException


class EnrollmentService:
    """Enrollment service with campus scope support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _enrich_with_scheduled_hours(self, enrollments: List[Enrollment]) -> List[EnrollmentResponse]:
        """为报名记录添加已排课时信息"""
        if not enrollments:
            return []

        # 获取所有班级计划ID
        class_plan_ids = list(set(e.class_plan_id for e in enrollments if e.class_plan_id))

        # 批量查询每个班级计划的已排课时总数（只统计scheduled状态，不含已完成的）
        scheduled_hours_map = {}
        if class_plan_ids:
            result = await self.db.execute(
                select(
                    Schedule.class_plan_id,
                    func.coalesce(func.sum(Schedule.lesson_hours), 0).label('total_hours')
                )
                .where(Schedule.class_plan_id.in_(class_plan_ids))
                .where(Schedule.status == 'scheduled')  # 只统计待上课的排课
                .group_by(Schedule.class_plan_id)
            )
            for row in result.fetchall():
                scheduled_hours_map[row[0]] = row[1]

        # 构建响应列表
        responses = []
        for enrollment in enrollments:
            response = EnrollmentResponse(
                id=enrollment.id,
                student_id=enrollment.student_id,
                class_plan_id=enrollment.class_plan_id,
                enroll_date=enrollment.enroll_date,
                paid_amount=enrollment.paid_amount,
                purchased_hours=enrollment.purchased_hours,
                used_hours=enrollment.used_hours,
                scheduled_hours=Decimal(str(scheduled_hours_map.get(enrollment.class_plan_id, 0))),
                status=enrollment.status,
                notes=enrollment.notes,
                created_time=enrollment.created_time,
                updated_time=enrollment.updated_time,
                student=enrollment.student,
                class_plan=enrollment.class_plan,
            )
            responses.append(response)

        return responses

    async def get_by_id(
        self,
        enrollment_id: int,
        campus_id_filter: Optional[int] = None
    ) -> Enrollment:
        """
        Get enrollment by ID.
        如果提供campus_id_filter，会检查报名是否属于该校区。
        """
        result = await self.db.execute(
            select(Enrollment)
            .options(
                selectinload(Enrollment.student),
                selectinload(Enrollment.class_plan)
            )
            .where(Enrollment.id == enrollment_id)
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise NotFoundException(f"报名记录不存在: {enrollment_id}")

        # 校区权限检查
        if campus_id_filter is not None and enrollment.campus_id != campus_id_filter:
            raise ForbiddenException("无权访问该报名记录")

        return enrollment

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[int] = None,
        class_plan_id: Optional[int] = None,
        status: Optional[str] = None,
        campus_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        enroll_date_from: Optional[str] = None,
        enroll_date_to: Optional[str] = None,
    ) -> Tuple[List[Enrollment], int]:
        """
        Get enrollments with pagination and filters.
        支持校区过滤、教师过滤和报名日期范围过滤。
        """
        query = select(Enrollment).options(
            selectinload(Enrollment.student),
            selectinload(Enrollment.class_plan)
        )

        # 校区过滤
        if campus_id is not None:
            query = query.where(Enrollment.campus_id == campus_id)

        # 教师过滤（教师只能看到自己负责班级的报名）
        if teacher_id is not None:
            query = query.join(ClassPlan, Enrollment.class_plan_id == ClassPlan.id)
            query = query.where(ClassPlan.teacher_id == teacher_id)

        if student_id:
            query = query.where(Enrollment.student_id == student_id)
        if class_plan_id:
            query = query.where(Enrollment.class_plan_id == class_plan_id)
        if status:
            query = query.where(Enrollment.status == status)
        # 报名日期范围过滤
        if enroll_date_from:
            query = query.where(Enrollment.enroll_date >= enroll_date_from)
        if enroll_date_to:
            query = query.where(Enrollment.enroll_date <= enroll_date_to)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        query = (
            query
            .order_by(Enrollment.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def create(
        self,
        data: EnrollmentCreate,
        created_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Enrollment:
        """
        Create enrollment and update related records.
        campus_id从ClassPlan自动获取。
        """
        # 获取班级计划并验证校区权限
        result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id == data.class_plan_id)
        )
        class_plan = result.scalar_one_or_none()
        if not class_plan:
            raise NotFoundException(f"开班计划不存在: {data.class_plan_id}")

        # 校区权限检查
        if campus_id_filter is not None and class_plan.campus_id != campus_id_filter:
            raise ForbiddenException("无权为该校区的班级创建报名")

        enrollment = Enrollment(
            student_id=data.student_id,
            class_plan_id=data.class_plan_id,
            campus_id=class_plan.campus_id,  # 从ClassPlan自动获取校区ID
            enroll_date=date.today(),
            paid_amount=data.paid_amount,
            purchased_hours=data.purchased_hours,
            used_hours=Decimal("0.0"),
            status=data.status,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(enrollment)

        # Update student hours and total paid
        result = await self.db.execute(
            select(Student).where(Student.id == data.student_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student.total_hours = Decimal(str(student.total_hours or 0)) + data.purchased_hours
            student.remaining_hours = Decimal(str(student.remaining_hours or 0)) + data.purchased_hours
            student.total_paid = Decimal(str(student.total_paid or 0)) + data.paid_amount
            # 更新学生状态为"已报名"
            student.status = "enrolled"
            student.updated_by = created_by

        # Update class plan current student count
        class_plan.current_students = (class_plan.current_students or 0) + 1

        await self.db.flush()

        # Reload with relationships
        return await self.get_by_id(enrollment.id)

    async def update(
        self,
        enrollment_id: int,
        data: EnrollmentUpdate,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Enrollment:
        """
        Update enrollment.
        如果提供campus_id_filter，会检查报名是否属于该校区。
        当报名状态变更为取消/退款时，联动更新学生状态为unenrolled。
        """
        enrollment = await self.get_by_id(enrollment_id, campus_id_filter=campus_id_filter)
        old_status = enrollment.status

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(enrollment, field, value)
        enrollment.updated_by = updated_by

        # 联动更新学生状态
        new_status = data.status
        if new_status in ("refunded", "cancelled") and old_status in ("active",):
            # 报名取消/退款，更新学生状态为"未报名"
            # 注意：需要检查学生是否还有其他有效的报名
            result = await self.db.execute(
                select(Enrollment)
                .where(Enrollment.student_id == enrollment.student_id)
                .where(Enrollment.status == "active")
                .where(Enrollment.id != enrollment_id)  # 排除当前报名
            )
            other_active = result.scalars().all()
            if not other_active:
                # 没有其他有效报名，更新学生状态
                result = await self.db.execute(
                    select(Student).where(Student.id == enrollment.student_id)
                )
                student = result.scalar_one_or_none()
                if student:
                    student.status = "unenrolled"
                    student.updated_by = updated_by

        await self.db.flush()
        return await self.get_by_id(enrollment_id)

    async def delete(
        self,
        enrollment_id: int,
        campus_id_filter: Optional[int] = None
    ) -> None:
        """
        Delete enrollment.
        如果提供campus_id_filter，会检查报名是否属于该校区。
        """
        enrollment = await self.get_by_id(enrollment_id, campus_id_filter=campus_id_filter)
        await self.db.delete(enrollment)

    async def get_class_plan_hours_summary(
        self,
        class_plan_id: int,
        campus_id_filter: Optional[int] = None
    ) -> dict:
        """
        获取班级计划的课时统计汇总，包含每个学生的详细课时信息。
        返回：每个学生的购买课时、已用课时、已排课时，以及全班最小可排课时。
        """
        # 校验班级计划存在
        result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id == class_plan_id)
        )
        class_plan = result.scalar_one_or_none()
        if not class_plan:
            raise NotFoundException(f"开班计划不存在: {class_plan_id}")

        # 校区权限检查
        if campus_id_filter is not None and class_plan.campus_id != campus_id_filter:
            raise ForbiddenException("无权访问该班级计划")

        # 查询该班级计划的已排课时总和（只统计scheduled状态的排课，班级共享）
        schedule_result = await self.db.execute(
            select(
                func.coalesce(func.sum(Schedule.lesson_hours), 0).label('scheduled_hours')
            )
            .where(Schedule.class_plan_id == class_plan_id)
            .where(Schedule.status == 'scheduled')
        )
        schedule_row = schedule_result.fetchone()
        class_scheduled_hours = Decimal(str(schedule_row[0])) if schedule_row else Decimal('0')

        # 查询该班级计划下所有有效报名的学生，包含每个学生的课时信息
        enrollment_result = await self.db.execute(
            select(Enrollment)
            .options(selectinload(Enrollment.student))
            .where(Enrollment.class_plan_id == class_plan_id)
            .where(Enrollment.status == 'active')
            .order_by(Enrollment.id)
        )
        enrollments = enrollment_result.scalars().all()

        # 构建每个学生的课时详情
        students = []
        min_available_hours = None

        for enrollment in enrollments:
            purchased = Decimal(str(enrollment.purchased_hours or 0))
            used = Decimal(str(enrollment.used_hours or 0))
            # 已排课时是班级共享的（同一个班级的排课对所有学生都算）
            scheduled = class_scheduled_hours
            available = purchased - used - scheduled

            student_info = {
                'student_id': enrollment.student_id,
                'student_name': enrollment.student.name if enrollment.student else f'学生{enrollment.student_id}',
                'purchased_hours': float(purchased),
                'used_hours': float(used),
                'scheduled_hours': float(scheduled),
                'available_hours': float(available),
            }
            students.append(student_info)

            # 记录最小可排课时
            if min_available_hours is None or available < min_available_hours:
                min_available_hours = available

        return {
            'class_plan_id': class_plan_id,
            'class_plan_name': class_plan.name,
            'class_scheduled_hours': float(class_scheduled_hours),  # 班级已排课时
            'students': students,
            'total_students': len(students),
            'min_available_hours': float(min_available_hours) if min_available_hours is not None else 0,
        }
