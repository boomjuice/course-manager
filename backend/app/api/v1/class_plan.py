"""
Class plan API endpoints with RBAC permission check and campus scope filter.
开班计划管理接口，支持校区数据隔离。
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import (
    DBSession, CampusScopedQuery,
    ClassPlanRead, ClassPlanEdit, ClassPlanDelete,
)
from app.services.class_plan_service import ClassPlanService
from app.schemas.class_plan import (
    ClassPlanCreate, ClassPlanUpdate, ClassPlanResponse,
    ClassPlanWithDetailsResponse, ClassPlanBriefResponse
)
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/class-plans", tags=["开班计划"])


def get_service(db: AsyncSession = Depends(get_db)) -> ClassPlanService:
    return ClassPlanService(db)


@router.get("", summary="获取开班列表")
async def get_class_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = Query(None, description="课程ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    campus_id: Optional[int] = Query(None, description="校区ID"),
    status: Optional[str] = Query(None, description="状态"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    start_date_from: Optional[str] = Query(None, description="开班日期起始"),
    start_date_to: Optional[str] = Query(None, description="开班日期截止"),
    db: DBSession = None,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanRead = None,  # 权限：class_plan:read
):
    """
    获取开班列表（分页）。
    校区管理员只能看到自己校区的开班计划。
    教师只能看到自己负责的班级。
    """
    # 校区范围过滤
    scope = CampusScopedQuery()
    effective_campus_id = scope.get_campus_filter(current_user)
    # 如果用户有校区限制，强制使用用户的校区ID
    if effective_campus_id is not None:
        campus_id = effective_campus_id

    # 教师只能看到自己负责的班级
    if scope.is_teacher(current_user):
        my_teacher_id = await scope.get_teacher_id_for_user(db, current_user)
        if my_teacher_id:
            teacher_id = my_teacher_id

    items, total = await service.get_all(
        page, page_size, course_id, teacher_id, campus_id, status, is_active, search,
        start_date_from=start_date_from, start_date_to=start_date_to
    )
    # Service返回的已经是ClassPlanWithDetailsResponse，直接用model_dump
    return success_response([item.model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/active", summary="获取进行中的开班")
async def get_active_class_plans(
    db: DBSession = None,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanRead = None,  # 权限：class_plan:read
):
    """获取所有进行中的开班计划（用于下拉选择）"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    # 教师只能看到自己负责的班级
    teacher_id = None
    if scope.is_teacher(current_user):
        teacher_id = await scope.get_teacher_id_for_user(db, current_user)

    items = await service.get_all_active(campus_id=campus_id, teacher_id=teacher_id)
    return success_response([ClassPlanBriefResponse.model_validate(item).model_dump() for item in items])


@router.get("/all", summary="获取所有开班下拉列表")
async def get_all_class_plans_dropdown(
    active_only: bool = True,
    db: DBSession = None,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanRead = None,  # 权限：class_plan:read
):
    """获取所有开班计划（用于下拉选择）"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    # 教师只能看到自己负责的班级
    teacher_id = None
    if scope.is_teacher(current_user):
        teacher_id = await scope.get_teacher_id_for_user(db, current_user)

    items = await service.get_all_dropdown(active_only, campus_id=campus_id, teacher_id=teacher_id)
    return success_response([ClassPlanBriefResponse.model_validate(item).model_dump() for item in items])


@router.get("/{plan_id}", summary="获取开班详情")
async def get_class_plan(
    plan_id: int,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanRead = None,  # 权限：class_plan:read
):
    """获取开班计划详情"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    plan = await service.get_by_id(plan_id, campus_id_filter=campus_id)
    return success_response(ClassPlanResponse.model_validate(plan).model_dump())


@router.post("", summary="创建开班计划")
async def create_class_plan(
    data: ClassPlanCreate,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanEdit = None,  # 权限：class_plan:edit
):
    """
    创建开班计划。
    校区管理员创建时自动关联到其所属校区。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    # 校区管理员强制使用其所属校区
    if campus_id is not None:
        data.campus_id = campus_id

    plan = await service.create(data, current_user.username)
    return success_response(ClassPlanResponse.model_validate(plan).model_dump())


@router.put("/{plan_id}", summary="更新开班计划")
async def update_class_plan(
    plan_id: int,
    data: ClassPlanUpdate,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanEdit = None,  # 权限：class_plan:edit
):
    """
    更新开班计划。
    校区管理员只能更新自己校区的开班计划。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    plan = await service.update(plan_id, data, current_user.username, campus_id_filter=campus_id)
    return success_response(ClassPlanResponse.model_validate(plan).model_dump())


@router.delete("/{plan_id}", summary="删除开班计划")
async def delete_class_plan(
    plan_id: int,
    service: ClassPlanService = Depends(get_service),
    current_user: ClassPlanDelete = None,  # 权限：class_plan:delete
):
    """
    删除开班计划。
    校区管理员只能删除自己校区的开班计划。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    await service.delete(plan_id, campus_id_filter=campus_id)
    return success_response({"message": "删除成功"})
