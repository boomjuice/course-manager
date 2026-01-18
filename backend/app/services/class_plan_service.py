"""
Class plan service with campus scope support.
开班计划服务层，支持校区数据隔离。
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_plan import ClassPlan
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.campus import Campus, Classroom
from app.schemas.class_plan import ClassPlanCreate, ClassPlanUpdate, ClassPlanWithDetailsResponse, ClassPlanBriefResponse, CourseBriefInfo
from app.core.exceptions import NotFoundException, ForbiddenException


class ClassPlanService:
    """Class plan service with campus scope support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        plan_id: int,
        campus_id_filter: Optional[int] = None
    ) -> ClassPlan:
        """
        Get class plan by ID.
        如果提供campus_id_filter，会检查开班计划是否属于该校区。
        """
        result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundException(f"开班计划不存在: {plan_id}")

        # 校区权限检查
        if campus_id_filter is not None and plan.campus_id != campus_id_filter:
            raise ForbiddenException("无权访问该开班计划")

        return plan

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        campus_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        start_date_from: Optional[str] = None,
        start_date_to: Optional[str] = None,
    ) -> Tuple[List[ClassPlanWithDetailsResponse], int]:
        """Get class plans with pagination and filters."""
        query = select(ClassPlan)

        if course_id:
            query = query.where(ClassPlan.course_id == course_id)
        if teacher_id:
            query = query.where(ClassPlan.teacher_id == teacher_id)
        if campus_id:
            query = query.where(ClassPlan.campus_id == campus_id)
        if status:
            query = query.where(ClassPlan.status == status)
        if is_active is not None:
            query = query.where(ClassPlan.is_active == is_active)
        if search:
            query = query.where(ClassPlan.name.ilike(f"%{search}%"))
        # 开班日期范围过滤
        if start_date_from:
            query = query.where(ClassPlan.start_date >= start_date_from)
        if start_date_to:
            query = query.where(ClassPlan.start_date <= start_date_to)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        query = (
            query
            .order_by(ClassPlan.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        plans = list(result.scalars().all())

        # Enrich with related names
        enriched = []
        for plan in plans:
            item = ClassPlanWithDetailsResponse.model_validate(plan)
            # Get related names
            if plan.course_id:
                course = await self.db.get(Course, plan.course_id)
                item.course_name = course.name if course else None
            if plan.teacher_id:
                teacher = await self.db.get(Teacher, plan.teacher_id)
                item.teacher_name = teacher.name if teacher else None
            if plan.campus_id:
                campus = await self.db.get(Campus, plan.campus_id)
                item.campus_name = campus.name if campus else None
            if plan.classroom_id:
                classroom = await self.db.get(Classroom, plan.classroom_id)
                item.classroom_name = classroom.name if classroom else None
            enriched.append(item)

        return enriched, total_count

    async def get_all_active(
        self,
        campus_id: Optional[int] = None,
        teacher_id: Optional[int] = None
    ) -> List[ClassPlanBriefResponse]:
        """Get all active class plans (for dropdowns)."""
        query = (
            select(ClassPlan)
            .where(ClassPlan.is_active == True)
            .where(ClassPlan.status.in_(["pending", "ongoing"]))
        )

        # 校区过滤
        if campus_id is not None:
            query = query.where(ClassPlan.campus_id == campus_id)

        # 教师过滤（教师只能看到自己负责的班级）
        if teacher_id is not None:
            query = query.where(ClassPlan.teacher_id == teacher_id)

        query = query.order_by(ClassPlan.name)
        result = await self.db.execute(query)
        plans = list(result.scalars().all())
        return await self._enrich_with_course(plans)

    async def get_all_dropdown(
        self,
        active_only: bool = True,
        campus_id: Optional[int] = None,
        teacher_id: Optional[int] = None
    ) -> List[ClassPlanBriefResponse]:
        """Get all class plans for dropdown."""
        query = select(ClassPlan)

        # 校区过滤
        if campus_id is not None:
            query = query.where(ClassPlan.campus_id == campus_id)

        # 教师过滤（教师只能看到自己负责的班级）
        if teacher_id is not None:
            query = query.where(ClassPlan.teacher_id == teacher_id)

        if active_only:
            query = query.where(ClassPlan.is_active == True)

        query = query.order_by(ClassPlan.name)
        result = await self.db.execute(query)
        plans = list(result.scalars().all())
        return await self._enrich_with_course(plans)

    async def _enrich_with_course(self, plans: List[ClassPlan]) -> List[ClassPlanBriefResponse]:
        """Enrich class plans with course info for dropdown/brief response."""
        enriched = []
        # Batch load all courses to avoid N+1 query
        course_ids = list(set(p.course_id for p in plans if p.course_id))
        courses_map = {}
        if course_ids:
            result = await self.db.execute(
                select(Course).where(Course.id.in_(course_ids))
            )
            courses = result.scalars().all()
            courses_map = {c.id: c for c in courses}

        for plan in plans:
            item = ClassPlanBriefResponse(
                id=plan.id,
                name=plan.name,
                course_id=plan.course_id,
                teacher_id=plan.teacher_id,  # 主讲教师，排课时自动带出
                classroom_id=plan.classroom_id,  # 默认教室，排课时自动带出
                status=plan.status,
                current_students=plan.current_students,  # 当前报名人数
                course=None,
            )
            if plan.course_id and plan.course_id in courses_map:
                course = courses_map[plan.course_id]
                item.course = CourseBriefInfo(
                    id=course.id,
                    name=course.name,
                    unit_price=course.unit_price,
                )
            enriched.append(item)
        return enriched

    async def create(self, data: ClassPlanCreate, created_by: str) -> ClassPlan:
        """Create class plan."""
        # Verify course exists
        course = await self.db.get(Course, data.course_id)
        if not course:
            raise NotFoundException(f"课程不存在: {data.course_id}")

        plan = ClassPlan(
            name=data.name,
            course_id=data.course_id,
            teacher_id=data.teacher_id,
            campus_id=data.campus_id,
            classroom_id=data.classroom_id,
            start_date=data.start_date,
            end_date=data.end_date,
            max_students=data.max_students,
            total_lessons=data.total_lessons,
            status=data.status,
            description=data.description,
            is_active=data.is_active,
            created_by=created_by,
        )
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def update(
        self,
        plan_id: int,
        data: ClassPlanUpdate,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> ClassPlan:
        """
        Update class plan.
        如果提供campus_id_filter，会检查开班计划是否属于该校区。
        当班级状态变更为进行中(ongoing)时，联动更新报名学生状态为上课中(studying)。
        当班级状态变更为已结班(completed)时，联动更新报名学生状态为已结业(graduated)。
        """
        plan = await self.get_by_id(plan_id, campus_id_filter=campus_id_filter)
        old_status = plan.status

        # Verify course exists if changed
        if data.course_id and data.course_id != plan.course_id:
            course = await self.db.get(Course, data.course_id)
            if not course:
                raise NotFoundException(f"课程不存在: {data.course_id}")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)
        plan.updated_by = updated_by

        # 联动更新学生状态
        new_status = data.status
        from app.models.enrollment import Enrollment

        if new_status == "ongoing" and old_status != "ongoing":
            # 班级开始进行中，更新报名学生为"上课中"
            result = await self.db.execute(
                select(Enrollment.id)
                .where(Enrollment.class_plan_id == plan_id)
                .where(Enrollment.status == "active")
            )
            enrollment_ids = [row[0] for row in result.fetchall()]
            if enrollment_ids:
                await self.db.execute(
                    Enrollment.__table__.update()
                    .where(Enrollment.id.in_(enrollment_ids))
                    .values(status="active")  # 报名状态保持active
                )
                # 批量更新学生状态
                result = await self.db.execute(
                    select(Enrollment.student_id)
                    .where(Enrollment.id.in_(enrollment_ids))
                    .distinct()
                )
                student_ids = [row[0] for row in result.fetchall() if row[0]]
                if student_ids:
                    await self.db.execute(
                        Student.__table__.update()
                        .where(Student.id.in_(student_ids))
                        .values(status="studying", updated_by=updated_by)
                    )

        elif new_status == "completed" and old_status != "completed":
            # 班级结班，更新报名学生为"已结业"
            result = await self.db.execute(
                select(Enrollment.id)
                .where(Enrollment.class_plan_id == plan_id)
                .where(Enrollment.status == "active")
            )
            enrollment_ids = [row[0] for row in result.fetchall()]
            if enrollment_ids:
                # 批量更新学生状态
                result = await self.db.execute(
                    select(Enrollment.student_id)
                    .where(Enrollment.id.in_(enrollment_ids))
                    .distinct()
                )
                student_ids = [row[0] for row in result.fetchall() if row[0]]
                if student_ids:
                    await self.db.execute(
                        Student.__table__.update()
                        .where(Student.id.in_(student_ids))
                        .values(status="graduated", updated_by=updated_by)
                    )

        await self.db.flush()
        return plan

    async def delete(
        self,
        plan_id: int,
        campus_id_filter: Optional[int] = None
    ) -> None:
        """
        Delete class plan.
        如果提供campus_id_filter，会检查开班计划是否属于该校区。
        """
        plan = await self.get_by_id(plan_id, campus_id_filter=campus_id_filter)
        await self.db.delete(plan)
