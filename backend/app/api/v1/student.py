"""
Student API endpoints with RBAC permission check and campus scope filter.
学生管理接口，支持校区数据隔离。
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import (
    DBSession, CampusScopedQuery,
    StudentRead, StudentEdit, StudentDelete,
)
from app.services.student_service import StudentService
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentBriefResponse
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/students", tags=["学生管理"])


def get_service(db: AsyncSession = Depends(get_db)) -> StudentService:
    return StudentService(db)


@router.get("", summary="获取学生列表")
async def get_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    campus_id: Optional[int] = Query(None, description="校区ID"),
    status: Optional[str] = Query(None, description="状态"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    grade: Optional[str] = Query(None, description="年级"),
    source: Optional[str] = Query(None, description="来源"),
    service: StudentService = Depends(get_service),
    current_user: StudentRead = None,  # 权限：student:read
):
    """
    获取学生列表（分页）。
    校区管理员只能看到自己校区的学生。
    """
    # 校区范围过滤
    scope = CampusScopedQuery()
    effective_campus_id = scope.get_campus_filter(current_user)
    # 如果用户有校区限制，强制使用用户的校区ID
    if effective_campus_id is not None:
        campus_id = effective_campus_id

    items, total = await service.get_all(
        page, page_size, status, is_active, search, campus_id=campus_id,
        grade=grade, source=source
    )
    return success_response([StudentResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/active", summary="获取所有在读学生")
async def get_active_students(
    service: StudentService = Depends(get_service),
    current_user: StudentRead = None,  # 权限：student:read
):
    """获取所有在读学生（用于下拉选择）"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    items = await service.get_all_active(campus_id=campus_id)
    return success_response([StudentResponse.model_validate(item).model_dump() for item in items])


@router.get("/all", summary="获取学生下拉列表")
async def get_all_students_dropdown(
    active_only: bool = True,
    service: StudentService = Depends(get_service),
    current_user: StudentRead = None,  # 权限：student:read
):
    """获取所有学生（用于下拉选择）"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    items = await service.get_all_dropdown(active_only, campus_id=campus_id)
    return success_response([StudentResponse.model_validate(item).model_dump() for item in items])


@router.get("/{student_id}", summary="获取学生详情")
async def get_student(
    student_id: int,
    service: StudentService = Depends(get_service),
    current_user: StudentRead = None,  # 权限：student:read
):
    """获取学生详情"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    student = await service.get_by_id(student_id, campus_id_filter=campus_id)
    return success_response(StudentResponse.model_validate(student).model_dump())


@router.post("", summary="创建学生")
async def create_student(
    data: StudentCreate,
    service: StudentService = Depends(get_service),
    current_user: StudentEdit = None,  # 权限：student:edit
):
    """
    创建学生。
    校区管理员创建学生时自动关联到其所属校区。
    """
    from app.core.exceptions import ForbiddenException

    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    # 校区管理员只能在自己校区创建学生
    if campus_id is not None:
        # 如果用户传了campus_id且不是自己的校区，拒绝操作
        if data.campus_id is not None and data.campus_id != campus_id:
            raise ForbiddenException(message="无权在其他校区创建学生")
        # 强制使用用户所属校区
        data.campus_id = campus_id

    student = await service.create(data, current_user.username)
    return success_response(StudentResponse.model_validate(student).model_dump())


@router.put("/{student_id}", summary="更新学生")
async def update_student(
    student_id: int,
    data: StudentUpdate,
    service: StudentService = Depends(get_service),
    current_user: StudentEdit = None,  # 权限：student:edit
):
    """
    更新学生。
    校区管理员只能更新自己校区的学生。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    student = await service.update(student_id, data, current_user.username, campus_id_filter=campus_id)
    return success_response(StudentResponse.model_validate(student).model_dump())


@router.delete("/{student_id}", summary="删除学生")
async def delete_student(
    student_id: int,
    service: StudentService = Depends(get_service),
    current_user: StudentDelete = None,  # 权限：student:delete
):
    """
    删除学生。
    校区管理员只能删除自己校区的学生。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    await service.delete(student_id, campus_id_filter=campus_id)
    return success_response({"message": "删除成功"})
