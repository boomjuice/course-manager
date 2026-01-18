"""
Campus and Classroom API endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import (
    CurrentUser, AdminUser, CampusRead, CampusEdit, CampusDelete,
    ClassroomRead, ClassroomEdit, ClassroomDelete,
    CampusScopedQuery, DBSession
)
from app.services.campus_service import CampusService
from app.schemas.campus import (
    CampusCreate, CampusUpdate, CampusResponse, CampusWithClassroomsResponse,
    ClassroomCreate, ClassroomUpdate, ClassroomResponse
)
from app.schemas.common import MessageResponse, success_response

router = APIRouter(tags=["校区管理"])
campus_scope = CampusScopedQuery()


def get_service(db: AsyncSession = Depends(get_db)) -> CampusService:
    return CampusService(db)


# ============ Campus Endpoints ============

@router.get("/campuses", summary="获取所有校区")
async def get_campuses(
    include_inactive: bool = False,
    service: CampusService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get all campuses with their classrooms."""
    items = await service.get_all_campuses(include_inactive)
    return success_response([CampusWithClassroomsResponse.model_validate(item).model_dump() for item in items])


@router.get("/campuses/all", summary="获取校区下拉列表")
async def get_all_campuses_dropdown(
    active_only: bool = True,
    service: CampusService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get all campuses for dropdown (no classrooms)."""
    items = await service.get_all_campuses_simple(active_only)
    return success_response([CampusResponse.model_validate(item).model_dump() for item in items])


@router.get("/campuses/{campus_id}", summary="获取校区详情")
async def get_campus(
    campus_id: int,
    service: CampusService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get campus by ID with classrooms."""
    campus = await service.get_campus_by_id(campus_id)
    return success_response(CampusWithClassroomsResponse.model_validate(campus).model_dump())


@router.post("/campuses", summary="创建校区")
async def create_campus(
    data: CampusCreate,
    service: CampusService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Create campus (admin only)."""
    campus = await service.create_campus(data, current_user.username)
    return success_response(CampusResponse.model_validate(campus).model_dump())


@router.put("/campuses/{campus_id}", summary="更新校区")
async def update_campus(
    campus_id: int,
    data: CampusUpdate,
    service: CampusService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Update campus (admin only)."""
    campus = await service.update_campus(campus_id, data, current_user.username)
    return success_response(CampusResponse.model_validate(campus).model_dump())


@router.delete("/campuses/{campus_id}", summary="删除校区")
async def delete_campus(
    campus_id: int,
    service: CampusService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Delete campus (admin only). This will also delete all classrooms."""
    await service.delete_campus(campus_id)
    return success_response({"message": "删除成功"})


@router.get("/campuses/{campus_id}/classrooms", summary="获取校区教室")
async def get_classrooms_by_campus(
    campus_id: int,
    active_only: bool = True,
    service: CampusService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get classrooms by campus ID."""
    items = await service.get_classrooms_by_campus(campus_id, active_only)
    return success_response([ClassroomResponse.model_validate(item).model_dump() for item in items])


@router.post("/campuses/{campus_id}/classrooms", summary="创建教室")
async def create_classroom(
    campus_id: int,
    data: ClassroomCreate,
    service: CampusService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Create classroom (admin only)."""
    classroom = await service.create_classroom(campus_id, data, current_user.username)
    return success_response(ClassroomResponse.model_validate(classroom).model_dump())


# ============ Classroom Endpoints ============

@router.get("/classrooms", summary="获取所有教室")
async def get_all_classrooms(
    active_only: bool = True,
    db: DBSession = None,
    current_user: ClassroomRead = None,
):
    """
    Get all classrooms filtered by user's campus scope.
    超管未选校区时返回全部，其他用户按校区过滤。
    """
    service = CampusService(db)
    campus_id = campus_scope.get_campus_filter(current_user)
    items = await service.get_all_classrooms(active_only, campus_id)
    return success_response([ClassroomResponse.model_validate(item).model_dump() for item in items])


@router.get("/classrooms/all", summary="获取教室下拉列表")
async def get_all_classrooms_dropdown(
    active_only: bool = True,
    db: DBSession = None,
    current_user: ClassroomRead = None,
):
    """
    Get classrooms for dropdown filtered by user's campus scope.
    超管未选校区时返回全部，其他用户按校区过滤。
    """
    service = CampusService(db)
    campus_id = campus_scope.get_campus_filter(current_user)
    items = await service.get_all_classrooms(active_only, campus_id)
    return success_response([ClassroomResponse.model_validate(item).model_dump() for item in items])


@router.put("/classrooms/{classroom_id}", summary="更新教室")
async def update_classroom(
    classroom_id: int,
    data: ClassroomUpdate,
    db: DBSession = None,
    current_user: ClassroomEdit = None,
):
    """Update classroom (requires classroom:edit permission)."""
    service = CampusService(db)
    classroom = await service.update_classroom(classroom_id, data, current_user.username)
    return success_response(ClassroomResponse.model_validate(classroom).model_dump())


@router.delete("/classrooms/{classroom_id}", summary="删除教室")
async def delete_classroom(
    classroom_id: int,
    db: DBSession = None,
    current_user: ClassroomDelete = None,
):
    """Delete classroom (requires classroom:delete permission)."""
    service = CampusService(db)
    await service.delete_classroom(classroom_id)
    return success_response({"message": "删除成功"})
