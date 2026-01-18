"""
Teacher API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import CurrentUser, AdminUser
from app.services.teacher_service import TeacherService
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse, TeacherBriefResponse
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/teachers", tags=["教师管理"])


def get_service(db: AsyncSession = Depends(get_db)) -> TeacherService:
    return TeacherService(db)


@router.get("", summary="获取教师列表")
async def get_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="状态"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    subjects: Optional[List[str]] = Query(None, description="科目过滤（多选）"),
    grade_levels: Optional[List[str]] = Query(None, description="年级过滤（多选）"),
    service: TeacherService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get teachers with pagination and filters."""
    items, total = await service.get_all(
        page, page_size, status, is_active, search,
        subjects=subjects, grade_levels=grade_levels
    )
    return success_response([TeacherResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/active", summary="获取所有在职教师")
async def get_active_teachers(
    service: TeacherService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get all active teachers (for dropdowns)."""
    items = await service.get_all_active()
    return success_response([TeacherBriefResponse.model_validate(item).model_dump() for item in items])


@router.get("/all", summary="获取所有教师下拉列表")
async def get_all_teachers_dropdown(
    active_only: bool = True,
    service: TeacherService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get all teachers for dropdown."""
    items = await service.get_all_dropdown(active_only)
    return success_response([TeacherBriefResponse.model_validate(item).model_dump() for item in items])


@router.get("/{teacher_id}", summary="获取教师详情")
async def get_teacher(
    teacher_id: int,
    service: TeacherService = Depends(get_service),
    _: CurrentUser = None,
):
    """Get teacher by ID."""
    teacher = await service.get_by_id(teacher_id)
    return success_response(TeacherResponse.model_validate(teacher).model_dump())


@router.post("", summary="创建教师")
async def create_teacher(
    data: TeacherCreate,
    service: TeacherService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Create teacher (admin only)."""
    teacher = await service.create(data, current_user.username)
    return success_response(TeacherResponse.model_validate(teacher).model_dump())


@router.put("/{teacher_id}", summary="更新教师")
async def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    service: TeacherService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Update teacher (admin only)."""
    teacher = await service.update(teacher_id, data, current_user.username)
    return success_response(TeacherResponse.model_validate(teacher).model_dump())


@router.delete("/{teacher_id}", summary="删除教师")
async def delete_teacher(
    teacher_id: int,
    service: TeacherService = Depends(get_service),
    current_user: AdminUser = None,
):
    """Delete teacher (admin only)."""
    await service.delete(teacher_id)
    return success_response({"message": "删除成功"})
