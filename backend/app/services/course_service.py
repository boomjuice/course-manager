"""
Course product service with campus scope support.
课程产品服务层，支持校区数据隔离。
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException


class CourseService:
    """Course product service with campus scope support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        course_id: int,
        campus_id_filter: Optional[int] = None
    ) -> Course:
        """
        Get course by ID.
        如果提供campus_id_filter，会检查课程是否属于该校区。
        """
        query = select(Course).options(selectinload(Course.campus)).where(Course.id == course_id)

        result = await self.db.execute(query)
        course = result.scalar_one_or_none()

        if not course:
            raise NotFoundException(f"课程不存在: {course_id}")

        # 校区权限检查
        if campus_id_filter is not None and course.campus_id != campus_id_filter:
            raise ForbiddenException("无权访问该课程信息")

        return course

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        level: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        campus_id: Optional[int] = None,
    ) -> Tuple[List[Course], int]:
        """
        Get courses with pagination and filters.
        支持校区过滤。
        """
        query = select(Course).options(selectinload(Course.campus))

        # 校区过滤
        if campus_id is not None:
            query = query.where(Course.campus_id == campus_id)

        # Apply filters
        if subject:
            query = query.where(Course.subject == subject)
        if grade_level:
            query = query.where(Course.grade_level == grade_level)
        if level:
            query = query.where(Course.level == level)
        if is_active is not None:
            query = query.where(Course.is_active == is_active)
        if search:
            query = query.where(
                Course.name.ilike(f"%{search}%") |
                Course.code.ilike(f"%{search}%")
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination and ordering
        query = (
            query
            .order_by(Course.sort_order, Course.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def get_all_active(self, campus_id: Optional[int] = None) -> List[Course]:
        """Get all active courses (for dropdowns)."""
        query = select(Course).where(Course.is_active == True)

        # 校区过滤
        if campus_id is not None:
            query = query.where(Course.campus_id == campus_id)

        query = query.order_by(Course.sort_order, Course.id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: CourseCreate, created_by: str) -> Course:
        """Create course."""
        # Check code uniqueness if provided (同一校区内编码唯一)
        if data.code:
            code_query = select(Course).where(Course.code == data.code)
            if data.campus_id:
                code_query = code_query.where(Course.campus_id == data.campus_id)
            existing = await self.db.execute(code_query)
            if existing.scalar_one_or_none():
                raise ConflictException(f"课程编码已存在: {data.code}")

        course = Course(
            name=data.name,
            code=data.code,
            subject=data.subject,
            grade_level=data.grade_level,
            level=data.level,
            unit_price=data.unit_price,
            description=data.description,
            objectives=data.objectives,
            target_audience=data.target_audience,
            is_active=data.is_active,
            sort_order=data.sort_order,
            campus_id=data.campus_id,  # 校区ID
            created_by=created_by,
        )
        self.db.add(course)
        await self.db.flush()
        return course

    async def update(
        self,
        course_id: int,
        data: CourseUpdate,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Course:
        """
        Update course.
        如果提供campus_id_filter，会检查课程是否属于该校区。
        """
        course = await self.get_by_id(course_id, campus_id_filter=campus_id_filter)

        # Check code uniqueness if changed (同一校区内编码唯一)
        if data.code and data.code != course.code:
            code_query = select(Course).where(Course.code == data.code, Course.id != course_id)
            if course.campus_id:
                code_query = code_query.where(Course.campus_id == course.campus_id)
            existing = await self.db.execute(code_query)
            if existing.scalar_one_or_none():
                raise ConflictException(f"课程编码已存在: {data.code}")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        course.updated_by = updated_by

        await self.db.flush()
        return course

    async def delete(
        self,
        course_id: int,
        campus_id_filter: Optional[int] = None
    ) -> None:
        """
        Delete course.
        如果提供campus_id_filter，会检查课程是否属于该校区。
        """
        course = await self.get_by_id(course_id, campus_id_filter=campus_id_filter)
        await self.db.delete(course)
