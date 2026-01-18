"""
Student service with campus scope support.
学生服务层，支持校区数据隔离。
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.core.security import get_password_hash


class StudentService:
    """Student service with campus scope support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        student_id: int,
        campus_id_filter: Optional[int] = None
    ) -> Student:
        """
        Get student by ID.
        如果提供campus_id_filter，会检查学生是否属于该校区。
        """
        query = select(Student).options(selectinload(Student.campus)).where(Student.id == student_id)

        result = await self.db.execute(query)
        student = result.scalar_one_or_none()

        if not student:
            raise NotFoundException(f"学生不存在: {student_id}")

        # 校区权限检查
        if campus_id_filter is not None and student.campus_id != campus_id_filter:
            raise ForbiddenException("无权访问该学生信息")

        return student

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        campus_id: Optional[int] = None,
        grade: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Tuple[List[Student], int]:
        """
        Get students with pagination and filters.
        支持校区过滤、年级过滤、来源过滤。
        """
        query = select(Student).options(selectinload(Student.campus))

        # 校区过滤
        if campus_id is not None:
            query = query.where(Student.campus_id == campus_id)

        if status:
            query = query.where(Student.status == status)
        if is_active is not None:
            query = query.where(Student.is_active == is_active)
        if grade:
            query = query.where(Student.grade == grade)
        if source:
            query = query.where(Student.source == source)
        if search:
            query = query.where(
                Student.name.ilike(f"%{search}%") |
                Student.phone.ilike(f"%{search}%") |
                Student.parent_phone.ilike(f"%{search}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        query = (
            query
            .order_by(Student.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def get_all_active(self, campus_id: Optional[int] = None) -> List[Student]:
        """Get all active students (for dropdowns)."""
        query = select(Student).where(Student.is_active == True)

        # 校区过滤
        if campus_id is not None:
            query = query.where(Student.campus_id == campus_id)

        query = query.order_by(Student.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_dropdown(
        self,
        active_only: bool = True,
        campus_id: Optional[int] = None
    ) -> List[Student]:
        """Get all students for dropdown."""
        query = select(Student).order_by(Student.name)

        # 校区过滤
        if campus_id is not None:
            query = query.where(Student.campus_id == campus_id)

        if active_only:
            query = query.where(Student.is_active == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: StudentCreate, created_by: str) -> Student:
        """
        Create student with auto-created user account.
        密码默认为手机号后6位。
        """
        user_id = data.user_id

        # 如果没有提供user_id，自动创建用户账号
        if not user_id:
            # 检查手机号是否已被占用
            existing_phone = await self.db.execute(
                select(User).where(User.phone == data.phone)
            )
            if existing_phone.scalar_one_or_none():
                raise ConflictException(f"手机号 '{data.phone}' 已被其他用户使用")

            # 使用手机号作为用户名
            username = f"s_{data.phone}"  # 学生前缀s_

            # 检查用户名是否已存在
            existing_user = await self.db.execute(
                select(User).where(User.username == username)
            )
            if existing_user.scalar_one_or_none():
                raise ConflictException(f"该手机号已创建过学生账号")

            # 密码为手机号后6位
            password = data.phone[-6:]
            hashed_password = get_password_hash(password)

            # 创建用户（关联校区）
            user = User(
                username=username,
                phone=data.phone,
                hashed_password=hashed_password,
                role="student",
                campus_id=data.campus_id,  # 用户也关联校区
                is_active=True,
                created_by=created_by,
                updated_by=created_by,
            )
            self.db.add(user)
            await self.db.flush()
            user_id = user.id

        student = Student(
            user_id=user_id,
            campus_id=data.campus_id,  # 校区ID
            name=data.name,
            gender=data.gender,
            birthday=data.birthday,
            phone=data.phone,
            parent_name=data.parent_name,
            parent_phone=data.parent_phone,
            school=data.school,
            grade=data.grade,
            address=data.address,
            source=data.source,
            subject_levels=data.subject_levels,
            learning_goals=data.learning_goals,
            remark=data.remark,
            status=data.status,
            is_active=data.is_active,
            created_by=created_by,
        )
        self.db.add(student)
        await self.db.flush()
        return student

    async def update(
        self,
        student_id: int,
        data: StudentUpdate,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Student:
        """
        Update student.
        如果提供campus_id_filter，会检查学生是否属于该校区。
        """
        student = await self.get_by_id(student_id, campus_id_filter=campus_id_filter)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)
        student.updated_by = updated_by

        await self.db.flush()
        return student

    async def delete(
        self,
        student_id: int,
        campus_id_filter: Optional[int] = None
    ) -> None:
        """
        Delete student.
        如果提供campus_id_filter，会检查学生是否属于该校区。
        """
        student = await self.get_by_id(student_id, campus_id_filter=campus_id_filter)
        await self.db.delete(student)

    async def update_status(
        self,
        student_id: int,
        status: str,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Student:
        """
        Update student status.

        Status values:
        - unenrolled: 未报名（没有有效报名或已取消/退款）
        - enrolled: 已报名（有有效报名，但班级未开始）
        - studying: 上课中（有正在进行的班级）
        - graduated: 已结业（所有班级都已完成）
        """
        valid_statuses = ["unenrolled", "enrolled", "studying", "graduated"]
        if status not in valid_statuses:
            raise ValueError(f"无效的学生状态: {status}，有效值: {', '.join(valid_statuses)}")

        student = await self.get_by_id(student_id, campus_id_filter=campus_id_filter)
        student.status = status
        student.updated_by = updated_by
        await self.db.flush()
        return student

    async def update_students_status_by_enrollment(
        self,
        enrollment_ids: list[int],
        status: str,
        updated_by: str
    ) -> int:
        """
        批量更新报名学生的状态。

        用于班级状态变更时联动更新学生状态：
        - 班级开始进行中 → 更新该班所有学生为 studying
        - 班级结班 → 更新该班所有学生为 graduated
        """
        valid_statuses = ["unenrolled", "enrolled", "studying", "graduated"]
        if status not in valid_statuses:
            raise ValueError(f"无效的学生状态: {status}")

        from app.models.enrollment import Enrollment

        # 查找这些报名记录对应的学生
        result = await self.db.execute(
            select(Enrollment.student_id)
            .where(Enrollment.id.in_(enrollment_ids))
            .distinct()
        )
        student_ids = [row[0] for row in result.fetchall() if row[0]]

        if not student_ids:
            return 0

        # 批量更新学生状态
        await self.db.execute(
            select(Student)
            .where(Student.id.in_(student_ids))
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(
            Student.__table__.update()
            .where(Student.id.in_(student_ids))
            .values(status=status, updated_by=updated_by)
        )
        await self.db.flush()

        return len(student_ids)

