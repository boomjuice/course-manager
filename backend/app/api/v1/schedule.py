"""
Schedule management API endpoints with RBAC permission check and campus scope filter.
排课管理接口，支持校区数据隔离和批次号操作。
"""
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Query
from sqlalchemy import select, func

from app.api.deps import (
    DBSession, CampusScopedQuery,
    ScheduleRead, ScheduleEdit, ScheduleDelete,
)
from app.models.enrollment import Enrollment
from app.models.student_attendance import StudentAttendance
from app.schemas.common import success_response, MessageResponse
from app.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    ScheduleListResponse, CalendarEventResponse,
    ScheduleBatchCreate, ScheduleBatchResponse, ScheduleBatchPreviewResponse, BatchConflictItem,
    ScheduleBatchUpdate, ScheduleBatchUpdateResponse, ScheduleBatchDeleteRequest,
    ConflictCheckRequest, ConflictCheckResponse,
)
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["排课管理"])


# Color mapping for different class plans
CALENDAR_COLORS = [
    "#3788d8",  # blue
    "#0ea5e9",  # sky
    "#10b981",  # green
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#8b5cf6",  # violet
    "#ec4899",  # pink
    "#06b6d4",  # cyan
]


def schedule_to_calendar_event(
    schedule,
    color_index: int = 0,
    student_count: int = 0,
    leave_count: int = 0,
    absent_count: int = 0,
) -> CalendarEventResponse:
    """Convert Schedule model to TOAST UI Calendar event format."""
    start_dt = datetime.combine(schedule.schedule_date, schedule.start_time)
    end_dt = datetime.combine(schedule.schedule_date, schedule.end_time)
    color = CALENDAR_COLORS[color_index % len(CALENDAR_COLORS)]

    title = schedule.title or (schedule.class_plan.name if schedule.class_plan else "课程")
    location = schedule.classroom.name if schedule.classroom else None
    teacher_name = schedule.teacher.name if schedule.teacher else None

    return CalendarEventResponse(
        id=str(schedule.id),
        calendarId=str(schedule.class_plan_id),
        title=title,
        category="time",
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        location=location,
        attendees=[teacher_name] if teacher_name else None,
        state=schedule.status,
        backgroundColor=color,
        borderColor=color,
        raw={
            "schedule_id": schedule.id,
            "class_plan_id": schedule.class_plan_id,
            "class_plan_name": schedule.class_plan.name if schedule.class_plan else None,
            "teacher_id": schedule.teacher_id,
            "teacher_name": teacher_name,
            "classroom_id": schedule.classroom_id,
            "classroom_name": location,
            "lesson_hours": schedule.lesson_hours,
            "status": schedule.status,
            "notes": schedule.notes,
            "student_count": student_count,
            "leave_count": leave_count,
            "absent_count": absent_count,
            "batch_no": schedule.batch_no,  # 批次号，有这个说明是批量创建的
        }
    )


@router.get("", summary="获取排课列表")
async def get_schedules(
    current_user: ScheduleRead,  # 权限：schedule:read
    db: DBSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    campus_id: Optional[int] = Query(None, description="校区ID"),
    class_plan_id: Optional[int] = Query(None, description="班级计划ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态"),
    batch_no: Optional[str] = Query(None, description="批次号"),
):
    """
    获取排课列表（分页）。
    - 校区管理员只能看到自己校区的排课
    - 教师只能看到自己的排课
    """
    # 校区范围过滤
    scope = CampusScopedQuery()
    effective_campus_id = scope.get_campus_filter(current_user)
    if effective_campus_id is not None:
        campus_id = effective_campus_id

    # 教师只能看到自己的排课
    if scope.is_teacher(current_user):
        my_teacher_id = await scope.get_teacher_id_for_user(db, current_user)
        if my_teacher_id:
            teacher_id = my_teacher_id

    service = ScheduleService(db)
    schedules, total = await service.get_schedules(
        page=page,
        page_size=page_size,
        class_plan_id=class_plan_id,
        teacher_id=teacher_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        campus_id=campus_id,
        batch_no=batch_no,
    )
    return success_response({
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [ScheduleResponse.model_validate(s).model_dump() for s in schedules],
    })


@router.get("/calendar", summary="获取日历事件")
async def get_calendar_events(
    current_user: ScheduleRead,  # 权限：schedule:read
    db: DBSession,
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    campus_id: Optional[int] = Query(None, description="校区ID"),
    class_plan_id: Optional[int] = Query(None, description="班级计划ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
):
    """
    获取日历视图排课数据。
    - 校区管理员只能看到自己校区的排课
    - 教师只能看到自己的排课
    """
    # 校区范围过滤
    scope = CampusScopedQuery()
    effective_campus_id = scope.get_campus_filter(current_user)
    if effective_campus_id is not None:
        campus_id = effective_campus_id

    # 教师只能看到自己的排课
    if scope.is_teacher(current_user):
        my_teacher_id = await scope.get_teacher_id_for_user(db, current_user)
        if my_teacher_id:
            teacher_id = my_teacher_id

    service = ScheduleService(db)
    schedules = await service.get_calendar_events(
        start_date=start_date,
        end_date=end_date,
        class_plan_id=class_plan_id,
        teacher_id=teacher_id,
        campus_id=campus_id,
    )

    # 批量获取各班级的在读学生数
    class_plan_ids = list(set(s.class_plan_id for s in schedules))
    schedule_ids = [s.id for s in schedules]
    student_count_map: Dict[int, int] = {}

    if class_plan_ids:
        result = await db.execute(
            select(
                Enrollment.class_plan_id,
                func.count(Enrollment.id).label("count")
            )
            .where(
                Enrollment.class_plan_id.in_(class_plan_ids),
                Enrollment.status == "active"
            )
            .group_by(Enrollment.class_plan_id)
        )
        for row in result:
            student_count_map[row.class_plan_id] = row.count

    # 批量获取每个排课的出勤统计（请假/缺勤人数）
    attendance_stats: Dict[int, Dict[str, int]] = {}
    if schedule_ids:
        result = await db.execute(
            select(
                StudentAttendance.schedule_id,
                StudentAttendance.status,
                func.count(StudentAttendance.id).label("count")
            )
            .where(StudentAttendance.schedule_id.in_(schedule_ids))
            .group_by(StudentAttendance.schedule_id, StudentAttendance.status)
        )
        for row in result:
            if row.schedule_id not in attendance_stats:
                attendance_stats[row.schedule_id] = {"leave": 0, "absent": 0}
            if row.status == "leave":
                attendance_stats[row.schedule_id]["leave"] = row.count
            elif row.status == "absent":
                attendance_stats[row.schedule_id]["absent"] = row.count

    # Create color index based on class_plan_id
    color_map = {}
    events = []
    for s in schedules:
        if s.class_plan_id not in color_map:
            color_map[s.class_plan_id] = len(color_map)
        student_count = student_count_map.get(s.class_plan_id, 0)
        stats = attendance_stats.get(s.id, {"leave": 0, "absent": 0})
        events.append(schedule_to_calendar_event(
            s,
            color_map[s.class_plan_id],
            student_count,
            leave_count=stats["leave"],
            absent_count=stats["absent"],
        ))

    return success_response([e.model_dump() for e in events])


@router.post("", summary="创建排课")
async def create_schedule(
    data: ScheduleCreate,
    current_user: ScheduleEdit,  # 权限：schedule:edit
    db: DBSession,
):
    """
    创建排课。
    校区管理员只能为自己校区的班级排课。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    schedule = await service.create_schedule(data, created_by=current_user.username, campus_id_filter=campus_id)
    return success_response(ScheduleResponse.model_validate(schedule).model_dump())


@router.post("/batch/preview", summary="预检测批量排课冲突")
async def batch_preview_schedules(
    data: ScheduleBatchCreate,
    current_user: ScheduleEdit,  # 权限：schedule:edit
    db: DBSession,
):
    """
    预检测批量排课的冲突情况，在实际创建前让用户确认。

    返回计划创建的总数量、有冲突的数量和冲突详情列表。
    用户查看后可选择：
    - 取消：不创建任何排课
    - 继续：跳过冲突的日期，创建其他排课
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    total_count, conflicts = await service.batch_preview_conflicts(
        data=data,
        campus_id_filter=campus_id,
    )

    return success_response({
        "total_count": total_count,
        "conflict_count": len(conflicts),
        "conflicts": [BatchConflictItem(**c).model_dump() for c in conflicts],
    })


@router.post("/batch", summary="批量排课")
async def batch_create_schedules(
    data: ScheduleBatchCreate,
    current_user: ScheduleEdit,  # 权限：schedule:edit
    db: DBSession,
):
    """
    批量创建周期性排课记录。
    会自动生成唯一的batch_no批次号，可用于后续批量操作。
    校区管理员只能为自己校区的班级排课。

    注意：建议先调用 /batch/preview 接口预检测冲突，让用户确认后再调用此接口。

    参数说明：
    - class_plan_id: 班级计划ID
    - date_ranges: 日期范围列表，支持多个不连续的时间段
    - time_slots: 时间段配置列表，每个时间段包含weekdays和start_time/end_time
    - lesson_hours: 每次课时数

    示例：
    ```json
    {
      "class_plan_id": 1,
      "date_ranges": [
        {"start_date": "2024-01-05", "end_date": "2024-01-20"},
        {"start_date": "2024-02-15", "end_date": "2024-02-28"}
      ],
      "time_slots": [
        {"weekdays": [0, 2, 4], "start_time": "09:00:00", "end_time": "11:00:00"},
        {"weekdays": [1, 3], "start_time": "14:00:00", "end_time": "16:00:00"}
      ],
      "lesson_hours": 2
    }
    ```
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    schedules, created_count, skipped_count, batch_no = await service.batch_create_schedules(
        data=data,
        created_by=current_user.username,
        campus_id_filter=campus_id,
    )
    return success_response({
        "created_count": created_count,
        "skipped_count": skipped_count,
        "batch_no": batch_no,
        "schedules": [ScheduleResponse.model_validate(s).model_dump() for s in schedules],
    })


# 批量操作路由必须放在动态路由 /{schedule_id} 前面，否则会路由冲突

@router.put("/batch", summary="批量更新排课")
async def batch_update_schedules(
    data: ScheduleBatchUpdate,
    current_user: ScheduleEdit,  # 权限：schedule:edit
    db: DBSession,
):
    """
    按ID列表批量更新排课。

    典型场景：用户在列表中勾选要修改的排课，然后批量更换教师/教室。

    参数说明：
    - schedule_ids: 要更新的排课ID列表（必填）
    - teacher_id: 新的教师ID（不传则不更新）
    - classroom_id: 新的教室ID（不传则不更新）
    - notes: 备注（不传则不更新）
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    count = await service.update_by_ids(
        schedule_ids=data.schedule_ids,
        data=data,
        updated_by=current_user.username,
        campus_id_filter=campus_id,
    )
    return success_response({"updated_count": count, "message": f"成功更新{count}条排课记录"})


@router.post("/batch-delete", summary="批量删除排课")
async def batch_delete_schedules(
    data: ScheduleBatchDeleteRequest,
    current_user: ScheduleDelete,  # 权限：schedule:delete
    db: DBSession,
):
    """
    按ID列表批量删除排课。

    典型场景：用户在列表中勾选要删除的排课。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    count = await service.delete_by_ids(
        schedule_ids=data.schedule_ids,
        campus_id_filter=campus_id,
    )
    return success_response({"message": f"成功删除{count}条排课记录"})


@router.get("/batch/{batch_no}", summary="获取批次排课列表")
async def get_batch_schedules(
    batch_no: str,
    current_user: ScheduleRead,  # 权限：schedule:read
    db: DBSession,
):
    """
    获取同一批次的所有排课记录。
    用于批量操作前查看该批次的排课详情。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    schedules = await service.get_batch_schedules(batch_no, campus_id_filter=campus_id)
    return success_response([ScheduleResponse.model_validate(s).model_dump() for s in schedules])


@router.delete("/batch/{batch_no}", summary="按批次号删除排课")
async def delete_schedules_by_batch(
    batch_no: str,
    current_user: ScheduleDelete,  # 权限：schedule:delete
    db: DBSession,
):
    """
    按批次号批量删除排课。
    校区管理员只能删除自己校区的排课。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    count = await service.delete_by_batch_no(batch_no, campus_id_filter=campus_id)
    return success_response({"message": f"成功删除{count}条排课记录"})


# 动态路由放在静态路由后面

@router.get("/{schedule_id}", summary="获取排课详情")
async def get_schedule(
    schedule_id: int,
    current_user: ScheduleRead,  # 权限：schedule:read
    db: DBSession,
):
    """获取排课详情"""
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    schedule = await service.get_schedule_by_id(schedule_id, campus_id_filter=campus_id)
    return success_response(ScheduleResponse.model_validate(schedule).model_dump())


@router.put("/{schedule_id}", summary="更新排课")
async def update_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    current_user: ScheduleEdit,  # 权限：schedule:edit
    db: DBSession,
):
    """
    更新排课。
    校区管理员只能更新自己校区的排课。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    schedule = await service.update_schedule(
        schedule_id=schedule_id,
        data=data,
        updated_by=current_user.username,
        campus_id_filter=campus_id,
    )
    return success_response(ScheduleResponse.model_validate(schedule).model_dump())


@router.delete("/{schedule_id}", summary="删除排课")
async def delete_schedule(
    schedule_id: int,
    current_user: ScheduleDelete,  # 权限：schedule:delete
    db: DBSession,
):
    """
    删除单条排课。
    校区管理员只能删除自己校区的排课。
    """
    scope = CampusScopedQuery()
    campus_id = scope.get_campus_filter(current_user)

    service = ScheduleService(db)
    await service.delete_schedule(schedule_id, campus_id_filter=campus_id)
    return success_response({"message": "删除成功"})


@router.post("/check-conflicts", summary="检测排课冲突")
async def check_schedule_conflicts(
    data: ConflictCheckRequest,
    current_user: ScheduleRead,  # 权限：schedule:read
    db: DBSession,
):
    """
    检测排课冲突。

    在创建或编辑排课前调用此接口，检测是否存在：
    - 教师冲突：同一教师在该时段已有其他排课
    - 教室冲突：同一教室在该时段已被占用

    编辑时传入 exclude_schedule_id 可排除当前编辑的排课记录。
    """
    service = ScheduleService(db)
    conflicts = await service.check_conflicts(data)
    return success_response(conflicts.model_dump())
