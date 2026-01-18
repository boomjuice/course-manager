"""
Campus and Classroom service - simple CRUD operations.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campus import Campus, Classroom
from app.schemas.campus import (
    CampusCreate, CampusUpdate,
    ClassroomCreate, ClassroomUpdate
)
from app.core.exceptions import NotFoundException, ConflictException


class CampusService:
    """Campus and Classroom service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ Campus Operations ============

    async def get_campus_by_id(self, campus_id: int) -> Campus:
        """Get campus by ID with classrooms."""
        result = await self.db.execute(
            select(Campus)
            .options(selectinload(Campus.classrooms))
            .where(Campus.id == campus_id)
        )
        campus = result.scalar_one_or_none()
        if not campus:
            raise NotFoundException(f"校区不存在: {campus_id}")
        return campus

    async def get_all_campuses(self, include_inactive: bool = False) -> List[Campus]:
        """Get all campuses."""
        query = (
            select(Campus)
            .options(selectinload(Campus.classrooms))
            .order_by(Campus.sort_order, Campus.id)
        )
        if not include_inactive:
            query = query.where(Campus.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_campuses_simple(self, active_only: bool = True) -> List[Campus]:
        """Get all campuses for dropdown (no classrooms)."""
        query = select(Campus).order_by(Campus.sort_order, Campus.id)
        if active_only:
            query = query.where(Campus.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_campus(self, data: CampusCreate, created_by: str) -> Campus:
        """Create campus with optional classrooms."""
        # Check name uniqueness
        existing = await self.db.execute(
            select(Campus).where(Campus.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"校区名称已存在: {data.name}")

        campus = Campus(
            name=data.name,
            address=data.address,
            phone=data.phone,
            contact_person=data.contact_person,
            description=data.description,
            is_active=data.is_active,
            sort_order=data.sort_order,
            created_by=created_by,
        )

        if data.classrooms:
            for i, cr_data in enumerate(data.classrooms):
                classroom = Classroom(
                    name=cr_data.name,
                    capacity=cr_data.capacity,
                    description=cr_data.description,
                    is_active=cr_data.is_active,
                    sort_order=cr_data.sort_order or i,
                    created_by=created_by,
                )
                campus.classrooms.append(classroom)

        self.db.add(campus)
        await self.db.flush()
        return campus

    async def update_campus(self, campus_id: int, data: CampusUpdate, updated_by: str) -> Campus:
        """Update campus."""
        campus = await self.get_campus_by_id(campus_id)

        # Check name uniqueness if changed
        if data.name and data.name != campus.name:
            existing = await self.db.execute(
                select(Campus).where(Campus.name == data.name, Campus.id != campus_id)
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"校区名称已存在: {data.name}")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campus, field, value)
        campus.updated_by = updated_by

        await self.db.flush()
        return campus

    async def delete_campus(self, campus_id: int) -> None:
        """Delete campus (cascade deletes classrooms)."""
        campus = await self.get_campus_by_id(campus_id)
        await self.db.delete(campus)

    # ============ Classroom Operations ============

    async def get_classroom_by_id(self, classroom_id: int) -> Classroom:
        """Get classroom by ID."""
        result = await self.db.execute(
            select(Classroom).where(Classroom.id == classroom_id)
        )
        classroom = result.scalar_one_or_none()
        if not classroom:
            raise NotFoundException(f"教室不存在: {classroom_id}")
        return classroom

    async def get_classrooms_by_campus(self, campus_id: int, active_only: bool = True) -> List[Classroom]:
        """Get classrooms by campus ID."""
        await self.get_campus_by_id(campus_id)
        query = (
            select(Classroom)
            .where(Classroom.campus_id == campus_id)
            .order_by(Classroom.sort_order, Classroom.id)
        )
        if active_only:
            query = query.where(Classroom.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_classrooms(
        self, active_only: bool = True, campus_id: Optional[int] = None
    ) -> List[Classroom]:
        """
        Get all classrooms, optionally filtered by campus.
        campus_id为None时返回所有校区的教室（超管未选校区时）。
        """
        query = select(Classroom).order_by(Classroom.campus_id, Classroom.sort_order, Classroom.id)
        if active_only:
            query = query.where(Classroom.is_active == True)
        if campus_id is not None:
            query = query.where(Classroom.campus_id == campus_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_classroom(self, campus_id: int, data: ClassroomCreate, created_by: str) -> Classroom:
        """Create classroom."""
        await self.get_campus_by_id(campus_id)

        classroom = Classroom(
            campus_id=campus_id,
            name=data.name,
            capacity=data.capacity,
            description=data.description,
            equipment=data.equipment,
            is_active=data.is_active,
            sort_order=data.sort_order,
            created_by=created_by,
        )
        self.db.add(classroom)
        await self.db.flush()
        # 刷新对象以获取数据库生成的字段（如created_time, updated_time）
        await self.db.refresh(classroom)
        return classroom

    async def update_classroom(self, classroom_id: int, data: ClassroomUpdate, updated_by: str) -> Classroom:
        """Update classroom."""
        classroom = await self.get_classroom_by_id(classroom_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(classroom, field, value)
        classroom.updated_by = updated_by

        await self.db.flush()
        # 刷新对象以获取更新后的字段
        await self.db.refresh(classroom)
        return classroom

    async def delete_classroom(self, classroom_id: int) -> None:
        """Delete classroom."""
        classroom = await self.get_classroom_by_id(classroom_id)
        await self.db.delete(classroom)
