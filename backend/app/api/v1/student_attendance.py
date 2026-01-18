"""
Student Attendance API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.student_attendance_service import StudentAttendanceService
from app.schemas.student_attendance import (
    StudentAttendanceResponse,
    LeaveApplicationCreate,
    AttendanceMarkRequest,
)
from app.schemas.common import success_response

router = APIRouter(prefix="/attendances", tags=["Student Attendance"])


@router.get("/student/{student_id}", summary="获取学生出勤记录")
async def get_student_attendances(
    student_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="出勤状态: normal/leave/absent"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get student's attendance records."""
    service = StudentAttendanceService(db)
    items, total = await service.get_student_attendance_list(
        student_id=student_id,
        page=page,
        page_size=page_size,
        status=status,
    )
    return success_response([StudentAttendanceResponse.model_validate(item).model_dump() for item in items], total=total, page=page, page_size=page_size)


@router.get("/schedule/{schedule_id}", summary="获取排课的学生出勤列表")
async def get_schedule_attendances(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get all students' attendance for a schedule."""
    service = StudentAttendanceService(db)
    items = await service.get_schedule_attendance_list(schedule_id)
    return success_response({"items": items})


@router.get("/upcoming/{student_id}", summary="获取学生未来排课（用于请假）")
async def get_upcoming_schedules(
    student_id: int,
    days: int = Query(7, ge=1, le=30, description="查询未来几天的排课"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get upcoming schedules for student to apply leave."""
    service = StudentAttendanceService(db)
    items = await service.get_upcoming_schedules_for_student(student_id, days)
    return success_response({"items": items})


@router.post("/leave", summary="学生申请请假")
async def apply_leave(
    data: LeaveApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student applies for leave."""
    # 如果是学生角色，只能给自己请假
    # 这里简化处理，管理员可以给任何学生请假
    # TODO: 实际应用中需要根据current_user.role判断
    service = StudentAttendanceService(db)

    # 从关联获取学生ID - 这里需要从enrollment获取
    # 简化：直接从请求参数获取student_id
    from sqlalchemy import select
    from app.models.enrollment import Enrollment
    from app.models.schedule import Schedule

    # 获取schedule关联的班级
    schedule_result = await db.execute(
        select(Schedule).where(Schedule.id == data.schedule_id)
    )
    schedule = schedule_result.scalar_one_or_none()
    if not schedule:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"排课不存在: {data.schedule_id}")

    # 如果是学生角色，需要验证是自己的课程
    if current_user.role == "student":
        from app.models.student import Student
        student_result = await db.execute(
            select(Student).where(Student.user_id == current_user.id)
        )
        student = student_result.scalar_one_or_none()
        if not student:
            from app.core.exceptions import BadRequestException
            raise BadRequestException("找不到关联的学生信息")
        student_id = student.id
    else:
        # 管理员需要从enrollment获取student_id
        # 这里需要传入enrollment_id或student_id参数
        from app.core.exceptions import BadRequestException
        raise BadRequestException("管理员请使用mark接口标记出勤")

    attendance = await service.apply_leave(
        student_id=student_id,
        schedule_id=data.schedule_id,
        leave_reason=data.leave_reason,
        applied_by=current_user.username,
    )
    await db.commit()
    return success_response(StudentAttendanceResponse.model_validate(attendance).model_dump())


@router.post("/leave/{student_id}", summary="为学生申请请假（管理员）")
async def apply_leave_for_student(
    student_id: int,
    data: LeaveApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin applies leave for a student."""
    service = StudentAttendanceService(db)
    attendance = await service.apply_leave(
        student_id=student_id,
        schedule_id=data.schedule_id,
        leave_reason=data.leave_reason,
        applied_by=current_user.username,
    )
    await db.commit()
    return success_response(StudentAttendanceResponse.model_validate(attendance).model_dump())


@router.post("/mark", summary="标记学生出勤状态")
async def mark_attendance(
    data: AttendanceMarkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark student attendance (admin only)."""
    service = StudentAttendanceService(db)
    attendance = await service.mark_attendance(data, current_user.username)
    await db.commit()
    return success_response(StudentAttendanceResponse.model_validate(attendance).model_dump())


@router.post("/batch-mark/{schedule_id}", summary="批量标记排课出勤")
async def batch_mark_attendance(
    schedule_id: int,
    items: list[AttendanceMarkRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch mark attendance for a schedule."""
    service = StudentAttendanceService(db)
    results = []
    for item in items:
        item.schedule_id = schedule_id  # 确保schedule_id一致
        attendance = await service.mark_attendance(item, current_user.username)
        results.append(StudentAttendanceResponse.model_validate(attendance).model_dump())
    await db.commit()
    return success_response({"items": results})
