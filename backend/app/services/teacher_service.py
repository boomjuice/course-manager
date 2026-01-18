"""
Teacher service.
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.core.exceptions import NotFoundException, ConflictException
from app.core.security import get_password_hash


class TeacherService:
    """Teacher service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, teacher_id: int) -> Teacher:
        """Get teacher by ID."""
        result = await self.db.execute(
            select(Teacher).where(Teacher.id == teacher_id)
        )
        teacher = result.scalar_one_or_none()
        if not teacher:
            raise NotFoundException(f"教师不存在: {teacher_id}")
        return teacher

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        subjects: Optional[List[str]] = None,
        grade_levels: Optional[List[str]] = None,
    ) -> Tuple[List[Teacher], int]:
        """Get teachers with pagination and filters."""
        query = select(Teacher)

        if status:
            query = query.where(Teacher.status == status)
        if is_active is not None:
            query = query.where(Teacher.is_active == is_active)
        if search:
            query = query.where(
                Teacher.name.ilike(f"%{search}%") |
                Teacher.phone.ilike(f"%{search}%")
            )
        # 科目过滤：使用 overlap 操作符检查是否有交集
        if subjects:
            query = query.where(Teacher.subjects.overlap(subjects))
        # 年级过滤：使用 overlap 操作符检查是否有交集
        if grade_levels:
            query = query.where(Teacher.grade_levels.overlap(grade_levels))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        query = (
            query
            .order_by(Teacher.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def get_all_active(self) -> List[Teacher]:
        """Get all active teachers (for dropdowns)."""
        result = await self.db.execute(
            select(Teacher)
            .where(Teacher.is_active == True)
            .order_by(Teacher.name)
        )
        return list(result.scalars().all())

    async def get_all_dropdown(self, active_only: bool = True) -> List[Teacher]:
        """Get all teachers for dropdown (optionally filtered by active status)."""
        query = select(Teacher)
        if active_only:
            query = query.where(Teacher.is_active == True)
        query = query.order_by(Teacher.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: TeacherCreate, created_by: str) -> Teacher:
        """
        Create teacher with auto-created user account.
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
            username = f"t_{data.phone}"  # 教师前缀t_

            # 检查用户名是否已存在
            existing_user = await self.db.execute(
                select(User).where(User.username == username)
            )
            if existing_user.scalar_one_or_none():
                raise ConflictException(f"该手机号已创建过教师账号")

            # 密码为手机号后6位
            password = data.phone[-6:]
            hashed_password = get_password_hash(password)

            # 创建用户
            user = User(
                username=username,
                phone=data.phone,
                hashed_password=hashed_password,
                role="teacher",
                is_active=True,
                created_by=created_by,
                updated_by=created_by,
            )
            self.db.add(user)
            await self.db.flush()
            user_id = user.id

        teacher = Teacher(
            user_id=user_id,
            name=data.name,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            id_card=data.id_card,
            entry_date=data.entry_date,
            education=data.education,
            major=data.major,
            subjects=data.subjects,
            grade_levels=data.grade_levels,
            hourly_rate=data.hourly_rate,
            introduction=data.introduction,
            status=data.status,
            is_active=data.is_active,
            created_by=created_by,
        )
        self.db.add(teacher)
        await self.db.flush()
        return teacher

    async def update(self, teacher_id: int, data: TeacherUpdate, updated_by: str) -> Teacher:
        """Update teacher."""
        teacher = await self.get_by_id(teacher_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(teacher, field, value)
        teacher.updated_by = updated_by

        await self.db.flush()
        return teacher

    async def delete(self, teacher_id: int) -> None:
        """Delete teacher."""
        teacher = await self.get_by_id(teacher_id)
        await self.db.delete(teacher)
