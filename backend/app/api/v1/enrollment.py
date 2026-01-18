"""
Enrollment API endpoints with RBAC permission check and campus scope filter.
报名管理接口，支持校区数据隔离。
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import (
    DBSession, CampusScopedQuery,
    EnrollmentRead, EnrollmentEdit, EnrollmentDelete,
)
from app.services.enrollment_service import EnrollmentService
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/enrollments", tags=["报名管理"])


def get_service(db: AsyncSession = Depends(get_db)) -> EnrollmentService:
    return EnrollmentService(db)


@router.get("", summary="获取报名列表")
async def get_enrollments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    campus_id: Optional[int] = Query(None, description="校区ID"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    class_plan_id: Optional[int] = Query(None, description="班级计划ID"),
    status: Optional[str] = Query(None, description="状态"),
    enroll_date_from: Optional[str] = Query(None, description="报名日期起始"),
    enroll_date_to: Optional[str] = Query(None, description="报名日期截止"),
    db: DBSession = None,
    service: EnrollmentService = Depends(get_service),
    current_user: EnrollmentRead = None,  # 权限：enrollment:read
):
    """
    获取报名列表（分页）。
    校区管理员只能看到自己校区的报名记录。
    教师只能看到自己负责班级的报名记录。
    响应中包含已排课时数(scheduled_hours)。
    """
    # 校区范围过滤
    scope = CampusScopedQuery()
    effective_campus_id = scope.get_campus_filter(current_user)
    # 如果用户有校区限制，强制使用用户的校区ID
    if effective_campus_id is not None:
        campus_id = effective_campus_id

    # 教师只能看到自己负责班级的报名
    teacher_id = None
    if scope.is_teacher(current_user):
        teacher_id = await scope.get_teacher_id_for_user(db, current_user)

    enrollments, total = await service.get_all(
        page, page_size, student_id, class_plan_id, status,
        campus_id=campus_id,
        teacher_id=teacher_id,
        enroll_date_from=enroll_date_from,
        enroll_date_to=enroll_date_to
    )
    # 丰富响应，添加已排课时信息
    items = await service._enrich_with_scheduled_hours(enrollments)
    return success_response([EnrollmentResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/class-plan/{class_plan_id}/hours-summary", summary="获取班级计划课时统计")
async def get_class_plan_hours_summary(
    class_plan_id: int,
    service: EnrollmentService = Depends(get_service),
    current_user: EnrollmentRead = None,  # 权限：enrollment:read
):
    """
    获取班级计划的课时统计汇总。
    返回：purchased_hours（购买课时总计）、used_hours（已用课时总计）、scheduled_hours（已排课时总计）、available_hours（可排课时）
    用于排课前校验课时是否超额。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    summary = await service.get_class_plan_hours_summary(class_plan_id, campus_id_filter=campus_id)
    return success_response(summary)


@router.get("/{enrollment_id}", summary="获取报名详情")
async def get_enrollment(
    enrollment_id: int,
    service: EnrollmentService = Depends(get_service),
    current_user: EnrollmentRead = None,  # 权限：enrollment:read
):
    """获取报名详情（包含已排课时数）"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    enrollment = await service.get_by_id(enrollment_id, campus_id_filter=campus_id)
    # 丰富响应，添加已排课时信息
    enriched = await service._enrich_with_scheduled_hours([enrollment])
    return success_response(EnrollmentResponse.model_validate(enriched[0]).model_dump() if enriched else None)


@router.post("", summary="创建报名")
async def create_enrollment(
    data: EnrollmentCreate,
    service: EnrollmentService = Depends(get_service),
    current_user: EnrollmentEdit = None,  # 权限：enrollment:edit
):
    """
    创建报名。
    校区管理员只能为自己校区的学生报名。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    enrollment = await service.create(data, created_by=current_user.username, campus_id_filter=campus_id)
    return success_response(EnrollmentResponse.model_validate(enrollment).model_dump())


@router.put("/{enrollment_id}", summary="更新报名")
async def update_enrollment(
    enrollment_id: int,
    data: EnrollmentUpdate,
    service: EnrollmentService = Depends(get_service),
    current_user: EnrollmentEdit = None,  # 权限：enrollment:edit
):
    """
    更新报名。
    校区管理员只能更新自己校区的报名记录。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    enrollment = await service.update(enrollment_id, data, updated_by=current_user.username, campus_id_filter=campus_id)
    return success_response(EnrollmentResponse.model_validate(enrollment).model_dump())


@router.delete("/{enrollment_id}", summary="删除报名")
async def delete_enrollment(
    enrollment_id: int,
    service: EnrollmentService = Depends(get_service),
    current_user: EnrollmentDelete = None,  # 权限：enrollment:delete
):
    """
    删除报名。
    校区管理员只能删除自己校区的报名记录。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)
    await service.delete(enrollment_id, campus_id_filter=campus_id)
    return success_response({"message": "删除成功"})
