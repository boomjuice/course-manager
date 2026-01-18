"""
Dictionary API endpoints.
Simple RESTful API, no bullshit complexity.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import CurrentUser, AdminUser
from app.services.dictionary_service import DictionaryService
from app.schemas.dictionary import (
    DictTypeCreate, DictTypeUpdate, DictTypeResponse, DictTypeWithItemsResponse,
    DictItemCreate, DictItemUpdate, DictItemResponse,
    DictItemBatchCreate, DictItemBatchUpdate
)
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/dict", tags=["数据字典"])


def get_service(db: AsyncSession = Depends(get_db)) -> DictionaryService:
    return DictionaryService(db)


# ============ DictType Endpoints ============

@router.get("/types", summary="获取所有字典类型")
async def get_dict_types(
    include_inactive: bool = False,
    service: DictionaryService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get all dictionary types."""
    items = await service.get_all_types(include_inactive)
    return success_response([DictTypeResponse.model_validate(item).model_dump() for item in items])


@router.get("/types/{type_id}", summary="获取字典类型详情")
async def get_dict_type(
    type_id: int,
    service: DictionaryService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get dictionary type with items by ID."""
    return success_response(DictTypeWithItemsResponse.model_validate(await service.get_type_by_id(type_id)).model_dump())


@router.get("/types/code/{code}", summary="按编码获取字典类型")
async def get_dict_type_by_code(
    code: str,
    service: DictionaryService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get dictionary type with items by code."""
    dict_type = await service.get_type_by_code(code)
    if not dict_type:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"字典类型不存在: {code}")
    return success_response(DictTypeResponse.model_validate(dict_type).model_dump())


@router.post("/types", summary="创建字典类型")
async def create_dict_type(
    data: DictTypeCreate,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Create dictionary type (admin only)."""
    return success_response(DictTypeResponse.model_validate(await service.create_type(data, current_user.username)).model_dump())


@router.put("/types/{type_id}", summary="更新字典类型")
async def update_dict_type(
    type_id: int,
    data: DictTypeUpdate,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Update dictionary type (admin only)."""
    return success_response(DictTypeResponse.model_validate(await service.update_type(type_id, data, current_user.username)).model_dump())


@router.delete("/types/{type_id}", summary="删除字典类型")
async def delete_dict_type(
    type_id: int,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Delete dictionary type (admin only). System types cannot be deleted."""
    await service.delete_type(type_id)
    return success_response(MessageResponse(message="删除成功").model_dump())


# ============ DictItem Endpoints ============

@router.get("/items/{type_code}", summary="获取字典项列表")
async def get_dict_items(
    type_code: str,
    active_only: bool = True,
    service: DictionaryService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get dictionary items by type code. This is the most commonly used endpoint."""
    items = await service.get_items_by_type_code(type_code, active_only)
    return success_response([DictItemResponse.model_validate(item).model_dump() for item in items])


@router.post("/types/{type_id}/items", summary="创建字典项")
async def create_dict_item(
    type_id: int,
    data: DictItemCreate,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Create dictionary item (admin only)."""
    return success_response(DictItemResponse.model_validate(await service.create_item(type_id, data, current_user.username)).model_dump())


@router.post("/types/{type_id}/items/batch", summary="批量创建字典项")
async def batch_create_dict_items(
    type_id: int,
    data: DictItemBatchCreate,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Batch create dictionary items (admin only)."""
    items = await service.batch_create_items(type_id, data.items, current_user.username)
    return success_response([DictItemResponse.model_validate(item).model_dump() for item in items])


@router.put("/items/{item_id}", summary="更新字典项")
async def update_dict_item(
    item_id: int,
    data: DictItemUpdate,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Update dictionary item (admin only)."""
    return success_response(DictItemResponse.model_validate(await service.update_item(item_id, data, current_user.username)).model_dump())


@router.delete("/items/{item_id}", summary="删除字典项")
async def delete_dict_item(
    item_id: int,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Delete dictionary item (admin only)."""
    await service.delete_item(item_id)
    return success_response(MessageResponse(message="删除成功").model_dump())


@router.post("/types/{type_id}/items/reorder", summary="重排序字典项")
async def reorder_dict_items(
    type_id: int,
    data: DictItemBatchUpdate,
    service: DictionaryService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Reorder dictionary items (admin only)."""
    await service.reorder_items(type_id, data.item_ids, current_user.username)
    return success_response(MessageResponse(message="排序更新成功").model_dump())
