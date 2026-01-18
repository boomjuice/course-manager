"""
Dictionary service for CRUD operations.
Keep it simple, stupid! No over-engineering here.
"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dictionary import DictType, DictItem
from app.schemas.dictionary import (
    DictTypeCreate, DictTypeUpdate,
    DictItemCreate, DictItemUpdate
)
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException


class DictionaryService:
    """Simple and clean dictionary service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ DictType Operations ============

    async def get_type_by_id(self, type_id: int) -> DictType:
        """Get dict type by ID."""
        result = await self.db.execute(
            select(DictType)
            .options(selectinload(DictType.items))
            .where(DictType.id == type_id)
        )
        dict_type = result.scalar_one_or_none()
        if not dict_type:
            raise NotFoundException(f"字典类型不存在: {type_id}")
        return dict_type

    async def get_type_by_code(self, code: str) -> Optional[DictType]:
        """Get dict type by code."""
        result = await self.db.execute(
            select(DictType)
            .options(selectinload(DictType.items))
            .where(DictType.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all_types(self, include_inactive: bool = False) -> List[DictType]:
        """Get all dict types."""
        query = select(DictType).order_by(DictType.sort_order, DictType.id)
        if not include_inactive:
            query = query.where(DictType.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_type(self, data: DictTypeCreate, created_by: str) -> DictType:
        """Create dict type with optional items."""
        # Check code uniqueness
        existing = await self.get_type_by_code(data.code)
        if existing:
            raise ConflictException(f"字典类型编码已存在: {data.code}")

        # Create type
        dict_type = DictType(
            code=data.code,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            sort_order=data.sort_order,
            is_system=False,
            created_by=created_by,
        )

        # Add items if provided
        if data.items:
            for i, item_data in enumerate(data.items):
                item = DictItem(
                    value=item_data.value,
                    label=item_data.label,
                    description=item_data.description,
                    color=item_data.color,
                    is_default=item_data.is_default,
                    is_active=item_data.is_active,
                    sort_order=item_data.sort_order or i,
                    created_by=created_by,
                )
                dict_type.items.append(item)

        self.db.add(dict_type)
        await self.db.flush()
        return dict_type

    async def update_type(self, type_id: int, data: DictTypeUpdate, updated_by: str) -> DictType:
        """Update dict type."""
        dict_type = await self.get_type_by_id(type_id)

        # Update fields if provided
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dict_type, field, value)
        dict_type.updated_by = updated_by

        await self.db.flush()
        return dict_type

    async def delete_type(self, type_id: int) -> None:
        """Delete dict type (cascade deletes items)."""
        dict_type = await self.get_type_by_id(type_id)
        if dict_type.is_system:
            raise BadRequestException("系统内置字典类型不可删除")
        await self.db.delete(dict_type)

    # ============ DictItem Operations ============

    async def get_item_by_id(self, item_id: int) -> DictItem:
        """Get dict item by ID."""
        result = await self.db.execute(
            select(DictItem).where(DictItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException(f"字典项不存在: {item_id}")
        return item

    async def get_items_by_type_code(self, type_code: str, active_only: bool = True) -> List[DictItem]:
        """Get items by type code - most commonly used method."""
        dict_type = await self.get_type_by_code(type_code)
        if not dict_type:
            raise NotFoundException(f"字典类型不存在: {type_code}")

        items = dict_type.items
        if active_only:
            items = [i for i in items if i.is_active]
        return sorted(items, key=lambda x: (x.sort_order, x.id))

    async def create_item(self, type_id: int, data: DictItemCreate, created_by: str) -> DictItem:
        """Create dict item."""
        # Verify type exists
        await self.get_type_by_id(type_id)

        item = DictItem(
            type_id=type_id,
            value=data.value,
            label=data.label,
            description=data.description,
            color=data.color,
            is_default=data.is_default,
            is_active=data.is_active,
            sort_order=data.sort_order,
            created_by=created_by,
        )

        # If this is default, unset other defaults
        if data.is_default:
            await self._unset_other_defaults(type_id)

        self.db.add(item)
        await self.db.flush()
        return item

    async def update_item(self, item_id: int, data: DictItemUpdate, updated_by: str) -> DictItem:
        """Update dict item."""
        item = await self.get_item_by_id(item_id)

        update_data = data.model_dump(exclude_unset=True)

        # Handle default flag
        if update_data.get("is_default"):
            await self._unset_other_defaults(item.type_id, exclude_id=item_id)

        for field, value in update_data.items():
            setattr(item, field, value)
        item.updated_by = updated_by

        await self.db.flush()
        return item

    async def delete_item(self, item_id: int) -> None:
        """Delete dict item."""
        item = await self.get_item_by_id(item_id)
        await self.db.delete(item)

    async def batch_create_items(self, type_id: int, items: List[DictItemCreate], created_by: str) -> List[DictItem]:
        """Batch create items for a type."""
        await self.get_type_by_id(type_id)

        created_items = []
        for i, item_data in enumerate(items):
            item = DictItem(
                type_id=type_id,
                value=item_data.value,
                label=item_data.label,
                description=item_data.description,
                color=item_data.color,
                is_default=item_data.is_default,
                is_active=item_data.is_active,
                sort_order=item_data.sort_order or i,
                created_by=created_by,
            )
            self.db.add(item)
            created_items.append(item)

        await self.db.flush()
        return created_items

    async def reorder_items(self, type_id: int, item_ids: List[int], updated_by: str) -> None:
        """Reorder items by setting sort_order based on list position."""
        await self.get_type_by_id(type_id)

        for order, item_id in enumerate(item_ids):
            result = await self.db.execute(
                select(DictItem).where(DictItem.id == item_id, DictItem.type_id == type_id)
            )
            item = result.scalar_one_or_none()
            if item:
                item.sort_order = order
                item.updated_by = updated_by

        await self.db.flush()

    async def _unset_other_defaults(self, type_id: int, exclude_id: Optional[int] = None) -> None:
        """Unset default flag for all items in a type except the excluded one."""
        query = select(DictItem).where(
            DictItem.type_id == type_id,
            DictItem.is_default == True
        )
        if exclude_id:
            query = query.where(DictItem.id != exclude_id)

        result = await self.db.execute(query)
        for item in result.scalars():
            item.is_default = False
