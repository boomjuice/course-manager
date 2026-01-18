"""
LessonRecord API - 课时消耗记录接口
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.lesson_record import LessonRecordResponse
from app.schemas.common import success_response
from app.services.lesson_record_service import LessonRecordService

router = APIRouter(prefix="/lesson-records", tags=["课时消耗记录"])


@router.get("/by-enrollment/{enrollment_id}", summary="获取报名记录的课时消耗历史")
async def get_records_by_enrollment(
    enrollment_id: int,
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取某个报名记录的课时消耗历史"""
    service = LessonRecordService(db)
    items, total = await service.get_by_enrollment(enrollment_id, page, page_size)
    return success_response([LessonRecordResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/by-student/{student_id}", summary="获取学生的课时消耗历史")
async def get_records_by_student(
    student_id: int,
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    class_plan_id: Optional[int] = Query(None, description="班级计划ID筛选"),
):
    """获取某个学生的所有课时消耗历史"""
    service = LessonRecordService(db)
    items, total = await service.get_by_student(student_id, page, page_size, class_plan_id)
    return success_response([LessonRecordResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)
