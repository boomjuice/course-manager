"""
Course product API endpoints with RBAC permission check and campus scope filter.
课程产品管理接口，支持校区数据隔离。
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import (
    DBSession, CampusScopedQuery,
    CourseRead, CourseEdit, CourseDelete,
)
from app.services.course_service import CourseService
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/courses", tags=["课程产品"])


def get_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    return CourseService(db)


@router.get("", summary="获取课程列表")
async def get_courses(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    campus_id: Optional[int] = Query(None, description="校区ID"),
    subject: Optional[str] = Query(None, description="学科"),
    grade_level: Optional[str] = Query(None, description="年级"),
    level: Optional[str] = Query(None, description="难度级别"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    service: CourseService = Depends(get_service),
    current_user: CourseRead = None,  # 权限：course:read
):
    """
    获取课程列表（分页）。
    校区管理员只能看到自己校区的课程。
    """
    # 校区范围过滤
    scope = CampusScopedQuery()
    effective_campus_id = scope.get_campus_filter(current_user)
    # 如果用户有校区限制，强制使用用户的校区ID
    if effective_campus_id is not None:
        campus_id = effective_campus_id

    items, total = await service.get_all(
        page, page_size, subject, grade_level, level, is_active, search,
        campus_id=campus_id
    )
    return success_response([CourseResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/active", summary="获取所有启用课程")
async def get_active_courses(
    service: CourseService = Depends(get_service),
    current_user: CourseRead = None,  # 权限：course:read
):
    """获取所有启用课程（用于下拉选择）"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    items = await service.get_all_active(campus_id=campus_id)
    return success_response([CourseResponse.model_validate(item).model_dump() for item in items])


@router.get("/{course_id}", summary="获取课程详情")
async def get_course(
    course_id: int,
    service: CourseService = Depends(get_service),
    current_user: CourseRead = None,  # 权限：course:read
):
    """获取课程详情"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    course = await service.get_by_id(course_id, campus_id_filter=campus_id)
    return success_response(CourseResponse.model_validate(course).model_dump())


@router.post("", summary="创建课程")
async def create_course(
    data: CourseCreate,
    service: CourseService = Depends(get_service),
    current_user: CourseEdit = None,  # 权限：course:edit
):
    """
    创建课程。
    校区管理员创建课程时自动关联到其所属校区。
    """
    from app.core.exceptions import ForbiddenException

    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    # 校区管理员只能在自己校区创建课程
    if campus_id is not None:
        # 如果用户传了campus_id且不是自己的校区，拒绝操作
        if data.campus_id is not None and data.campus_id != campus_id:
            raise ForbiddenException(message="无权在其他校区创建课程")
        # 强制使用用户所属校区
        data.campus_id = campus_id

    course = await service.create(data, current_user.username)
    return success_response(CourseResponse.model_validate(course).model_dump())


@router.put("/{course_id}", summary="更新课程")
async def update_course(
    course_id: int,
    data: CourseUpdate,
    service: CourseService = Depends(get_service),
    current_user: CourseEdit = None,  # 权限：course:edit
):
    """
    更新课程。
    校区管理员只能更新自己校区的课程。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    course = await service.update(course_id, data, current_user.username, campus_id_filter=campus_id)
    return success_response(CourseResponse.model_validate(course).model_dump())


@router.delete("/{course_id}", summary="删除课程")
async def delete_course(
    course_id: int,
    service: CourseService = Depends(get_service),
    current_user: CourseDelete = None,  # 权限：course:delete
):
    """
    删除课程。
    校区管理员只能删除自己校区的课程。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    await service.delete(course_id, campus_id_filter=campus_id)
    return success_response({"message": "删除成功"})
