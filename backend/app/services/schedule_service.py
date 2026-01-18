"""
Schedule service for CRUD operations with campus scope support.
排课服务层，支持校区数据隔离和批次号操作。
"""
import uuid
from datetime import date, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.schedule import Schedule
from app.models.class_plan import ClassPlan
from app.models.teacher import Teacher
from app.models.campus import Classroom
from app.models.enrollment import Enrollment
from app.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleBatchCreate, ScheduleBatchUpdate,
    ConflictCheckRequest, ConflictCheckResponse, ConflictDetail
)
from app.services.lesson_record_service import LessonRecordService


class ScheduleService:
    """Service for handling schedule operations with campus scope support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_batch_no(self) -> str:
        """生成唯一的批次号"""
        return f"BATCH-{uuid.uuid4().hex[:12].upper()}"

    async def create_schedule(
        self,
        data: ScheduleCreate,
        created_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Schedule:
        """
        Create a new schedule.
        campus_id从ClassPlan自动获取。
        """
        # Verify class plan exists and get campus_id
        result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id == data.class_plan_id)
        )
        class_plan = result.scalar_one_or_none()
        if not class_plan:
            raise NotFoundException(f"班级计划ID {data.class_plan_id} 不存在")

        # 校区权限检查
        if campus_id_filter is not None and class_plan.campus_id != campus_id_filter:
            raise ForbiddenException("无权为该校区的班级创建排课")

        schedule = Schedule(
            class_plan_id=data.class_plan_id,
            campus_id=class_plan.campus_id,  # 从ClassPlan自动获取校区ID
            teacher_id=data.teacher_id,
            classroom_id=data.classroom_id,
            schedule_date=data.schedule_date,
            start_time=data.start_time,
            end_time=data.end_time,
            lesson_hours=data.lesson_hours,
            title=data.title,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(schedule)
        await self.db.flush()
        await self.db.refresh(schedule)

        # Load relationships
        return await self.get_schedule_by_id(schedule.id)

    async def get_schedule_by_id(
        self,
        schedule_id: int,
        campus_id_filter: Optional[int] = None
    ) -> Schedule:
        """
        Get schedule by ID with relationships.
        如果提供campus_id_filter，会检查排课是否属于该校区。
        """
        result = await self.db.execute(
            select(Schedule)
            .options(
                selectinload(Schedule.class_plan),
                selectinload(Schedule.teacher),
                selectinload(Schedule.classroom),
            )
            .where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise NotFoundException(f"排课记录ID {schedule_id} 不存在")

        # 校区权限检查
        if campus_id_filter is not None and schedule.campus_id != campus_id_filter:
            raise ForbiddenException("无权访问该排课记录")

        return schedule

    async def get_schedules(
        self,
        page: int = 1,
        page_size: int = 20,
        class_plan_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        campus_id: Optional[int] = None,
        batch_no: Optional[str] = None,
    ) -> tuple[List[Schedule], int]:
        """
        Get paginated list of schedules with filters.
        支持校区过滤和批次号过滤。
        """
        query = select(Schedule).options(
            selectinload(Schedule.class_plan),
            selectinload(Schedule.teacher),
            selectinload(Schedule.classroom),
        )

        # 校区过滤
        if campus_id is not None:
            query = query.where(Schedule.campus_id == campus_id)

        # Apply filters
        if class_plan_id:
            query = query.where(Schedule.class_plan_id == class_plan_id)
        if teacher_id:
            query = query.where(Schedule.teacher_id == teacher_id)
        if start_date:
            query = query.where(Schedule.schedule_date >= start_date)
        if end_date:
            query = query.where(Schedule.schedule_date <= end_date)
        if status:
            query = query.where(Schedule.status == status)
        if batch_no:
            query = query.where(Schedule.batch_no == batch_no)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Schedule.schedule_date.desc(), Schedule.start_time).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        schedules = list(result.scalars().all())

        return schedules, total

    async def get_calendar_events(
        self,
        start_date: date,
        end_date: date,
        class_plan_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        campus_id: Optional[int] = None,
    ) -> List[Schedule]:
        """
        Get schedules for calendar view (no pagination).
        支持校区过滤。
        """
        query = select(Schedule).options(
            selectinload(Schedule.class_plan),
            selectinload(Schedule.teacher),
            selectinload(Schedule.classroom),
        ).where(
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date,
        )

        # 校区过滤
        if campus_id is not None:
            query = query.where(Schedule.campus_id == campus_id)

        if class_plan_id:
            query = query.where(Schedule.class_plan_id == class_plan_id)
        if teacher_id:
            query = query.where(Schedule.teacher_id == teacher_id)

        query = query.order_by(Schedule.schedule_date, Schedule.start_time)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_schedule(
        self,
        schedule_id: int,
        data: ScheduleUpdate,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> Schedule:
        """
        Update schedule information.
        如果提供campus_id_filter，会检查排课是否属于该校区。
        """
        schedule = await self.get_schedule_by_id(schedule_id, campus_id_filter=campus_id_filter)
        old_status = schedule.status
        update_dict = data.model_dump(exclude_unset=True)
        update_dict["updated_by"] = updated_by

        # 检查状态变化，处理课时消耗
        new_status = update_dict.get("status", old_status)
        lesson_record_service = LessonRecordService(self.db)

        if old_status != "completed" and new_status == "completed":
            # 状态变为已完成，创建课时消耗记录
            # 先更新状态
            await self.db.execute(
                update(Schedule).where(Schedule.id == schedule_id).values(**update_dict)
            )
            await self.db.refresh(schedule)
            # 创建消耗记录
            await lesson_record_service.create_from_schedule(schedule, updated_by)
        elif old_status == "completed" and new_status != "completed":
            # 状态从已完成变回其他状态，撤销课时消耗
            await lesson_record_service.reverse_from_schedule(schedule, updated_by)
            await self.db.execute(
                update(Schedule).where(Schedule.id == schedule_id).values(**update_dict)
            )
            await self.db.refresh(schedule)
        else:
            # 普通更新
            if update_dict:
                await self.db.execute(
                    update(Schedule).where(Schedule.id == schedule_id).values(**update_dict)
                )
                await self.db.refresh(schedule)

        return await self.get_schedule_by_id(schedule_id)

    async def delete_schedule(
        self,
        schedule_id: int,
        campus_id_filter: Optional[int] = None
    ) -> None:
        """
        Delete a schedule.
        如果提供campus_id_filter，会检查排课是否属于该校区。
        已完成的排课不允许删除。
        """
        schedule = await self.get_schedule_by_id(schedule_id, campus_id_filter=campus_id_filter)

        # 已完成的排课不允许删除
        if schedule.status == 'completed':
            raise BadRequestException("已完成的排课不能删除")

        await self.db.execute(
            delete(Schedule).where(Schedule.id == schedule_id)
        )

    async def delete_by_batch_no(
        self,
        batch_no: str,
        campus_id_filter: Optional[int] = None
    ) -> int:
        """
        按批次号批量删除排课。
        如果提供campus_id_filter，只删除该校区的排课。
        已完成的排课不会被删除。
        返回删除的记录数。
        """
        query = delete(Schedule).where(
            Schedule.batch_no == batch_no,
            Schedule.status != 'completed'  # 已完成的排课不能删除
        )

        # 校区过滤
        if campus_id_filter is not None:
            query = query.where(Schedule.campus_id == campus_id_filter)

        result = await self.db.execute(query)
        return result.rowcount

    async def update_by_ids(
        self,
        schedule_ids: List[int],
        data: ScheduleBatchUpdate,
        updated_by: str,
        campus_id_filter: Optional[int] = None
    ) -> int:
        """
        按排课ID列表批量更新排课。
        返回更新的记录数。
        """
        # 构建更新条件
        conditions = [Schedule.id.in_(schedule_ids)]

        # 校区过滤
        if campus_id_filter is not None:
            conditions.append(Schedule.campus_id == campus_id_filter)

        # 构建更新字段（只更新传入的字段）
        update_values = {"updated_by": updated_by}
        if data.teacher_id is not None:
            update_values["teacher_id"] = data.teacher_id
        if data.classroom_id is not None:
            update_values["classroom_id"] = data.classroom_id
        if data.notes is not None:
            update_values["notes"] = data.notes

        # 如果没有要更新的字段，直接返回0
        if len(update_values) == 1:  # 只有 updated_by
            return 0

        query = update(Schedule).where(*conditions).values(**update_values)
        result = await self.db.execute(query)
        return result.rowcount

    async def delete_by_ids(
        self,
        schedule_ids: List[int],
        campus_id_filter: Optional[int] = None
    ) -> int:
        """
        按排课ID列表批量删除排课。
        已完成的排课不会被删除。
        返回删除的记录数。
        """
        conditions = [
            Schedule.id.in_(schedule_ids),
            Schedule.status != 'completed'  # 已完成的排课不能删除
        ]

        # 校区过滤
        if campus_id_filter is not None:
            conditions.append(Schedule.campus_id == campus_id_filter)

        query = delete(Schedule).where(*conditions)
        result = await self.db.execute(query)
        return result.rowcount

    async def get_batch_schedules(
        self,
        batch_no: str,
        campus_id_filter: Optional[int] = None
    ) -> List[Schedule]:
        """
        获取同一批次的所有排课，用于前端显示批次详情。
        """
        query = (
            select(Schedule)
            .options(
                selectinload(Schedule.class_plan),
                selectinload(Schedule.teacher),
                selectinload(Schedule.classroom),
            )
            .where(Schedule.batch_no == batch_no)
            .order_by(Schedule.schedule_date, Schedule.start_time)
        )

        if campus_id_filter is not None:
            query = query.where(Schedule.campus_id == campus_id_filter)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _build_schedules_to_create(self, data: ScheduleBatchCreate) -> list:
        """
        根据批量创建参数，生成所有要创建的排课列表（去重）。
        返回: [{'schedule_date': date, 'start_time': time, 'end_time': time}, ...]
        """
        # 构建 weekday -> time_slots 映射
        weekday_to_slots: dict[int, list] = {}
        for slot in data.time_slots:
            for weekday in slot.weekdays:
                if weekday not in weekday_to_slots:
                    weekday_to_slots[weekday] = []
                weekday_to_slots[weekday].append(slot)

        # 收集所有要创建的排课，用set去重
        schedule_keys: set = set()
        schedules_to_create: list = []

        for date_range in data.date_ranges:
            current_date = date_range.start_date
            while current_date <= date_range.end_date:
                weekday = current_date.weekday()
                if weekday in weekday_to_slots:
                    for slot in weekday_to_slots[weekday]:
                        key = (current_date, slot.start_time, slot.end_time)
                        if key not in schedule_keys:
                            schedule_keys.add(key)
                            schedules_to_create.append({
                                'schedule_date': current_date,
                                'start_time': slot.start_time,
                                'end_time': slot.end_time,
                            })
                current_date += timedelta(days=1)

        return schedules_to_create

    async def batch_preview_conflicts(
        self,
        data: ScheduleBatchCreate,
        campus_id_filter: Optional[int] = None
    ) -> Tuple[int, list]:
        """
        预检测批量创建的冲突。
        返回: (total_count, conflicts)
        conflicts: [{'schedule_date', 'start_time', 'end_time', 'conflict_type', 'conflict_with'}, ...]
        """
        # Verify class plan exists
        result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id == data.class_plan_id)
        )
        class_plan = result.scalar_one_or_none()
        if not class_plan:
            raise NotFoundException(f"班级计划ID {data.class_plan_id} 不存在")

        if campus_id_filter is not None and class_plan.campus_id != campus_id_filter:
            raise ForbiddenException("无权为该校区的班级创建排课")

        schedules_to_create = self._build_schedules_to_create(data)
        conflicts = []

        # 获取教师和教室名称
        teacher_name = None
        classroom_name = None
        if data.teacher_id:
            teacher = await self.db.get(Teacher, data.teacher_id)
            teacher_name = teacher.name if teacher else f"教师#{data.teacher_id}"
        if data.classroom_id:
            classroom = await self.db.get(Classroom, data.classroom_id)
            classroom_name = classroom.name if classroom else f"教室#{data.classroom_id}"

        for sched_info in schedules_to_create:
            # 检测教师冲突
            if data.teacher_id:
                query = (
                    select(Schedule)
                    .options(selectinload(Schedule.class_plan))
                    .where(
                        Schedule.schedule_date == sched_info['schedule_date'],
                        Schedule.start_time < sched_info['end_time'],
                        Schedule.end_time > sched_info['start_time'],
                        Schedule.teacher_id == data.teacher_id,
                        Schedule.status != 'cancelled',
                    ).limit(1)
                )
                result = await self.db.execute(query)
                conflict_schedule = result.scalar_one_or_none()
                if conflict_schedule:
                    class_name = conflict_schedule.class_plan.name if conflict_schedule.class_plan else "未知班级"
                    conflicts.append({
                        'schedule_date': sched_info['schedule_date'],
                        'start_time': sched_info['start_time'],
                        'end_time': sched_info['end_time'],
                        'conflict_type': 'teacher',
                        'conflict_with': f"教师【{teacher_name}】已有排课：{class_name}",
                    })
                    continue  # 已有教师冲突，不再检测教室

            # 检测教室冲突
            if data.classroom_id:
                query = (
                    select(Schedule)
                    .options(selectinload(Schedule.class_plan))
                    .where(
                        Schedule.schedule_date == sched_info['schedule_date'],
                        Schedule.start_time < sched_info['end_time'],
                        Schedule.end_time > sched_info['start_time'],
                        Schedule.classroom_id == data.classroom_id,
                        Schedule.status != 'cancelled',
                    ).limit(1)
                )
                result = await self.db.execute(query)
                conflict_schedule = result.scalar_one_or_none()
                if conflict_schedule:
                    class_name = conflict_schedule.class_plan.name if conflict_schedule.class_plan else "未知班级"
                    conflicts.append({
                        'schedule_date': sched_info['schedule_date'],
                        'start_time': sched_info['start_time'],
                        'end_time': sched_info['end_time'],
                        'conflict_type': 'classroom',
                        'conflict_with': f"教室【{classroom_name}】已被占用：{class_name}",
                    })

        return len(schedules_to_create), conflicts

    async def batch_create_schedules(
        self,
        data: ScheduleBatchCreate,
        created_by: str,
        campus_id_filter: Optional[int] = None,
        skip_conflicts: bool = True
    ) -> Tuple[List[Schedule], int, int, str]:
        """
        Batch create schedules based on weekday pattern with multiple time slots.
        自动生成batch_no批次号，campus_id从ClassPlan自动获取。

        参数:
        - skip_conflicts: True则跳过冲突继续创建，False则有冲突时不创建任何记录

        返回: (schedules, created_count, skipped_count, batch_no)
        """
        # Verify class plan exists and get campus_id
        result = await self.db.execute(
            select(ClassPlan).where(ClassPlan.id == data.class_plan_id)
        )
        class_plan = result.scalar_one_or_none()
        if not class_plan:
            raise NotFoundException(f"班级计划ID {data.class_plan_id} 不存在")

        if campus_id_filter is not None and class_plan.campus_id != campus_id_filter:
            raise ForbiddenException("无权为该校区的班级创建排课")

        batch_no = self._generate_batch_no()
        schedules_to_create = self._build_schedules_to_create(data)

        # 检测冲突并创建
        skipped_count = 0
        created_schedules: List[Schedule] = []
        max_count = data.max_count  # 最大创建数量（课时限制场景）

        for sched_info in schedules_to_create:
            # 如果设置了max_count且已创建数量达到限制，停止创建
            if max_count is not None and len(created_schedules) >= max_count:
                skipped_count += 1
                continue
            has_conflict = False

            # 检测教师冲突
            if data.teacher_id:
                teacher_conflict_query = select(Schedule.id).where(
                    Schedule.schedule_date == sched_info['schedule_date'],
                    Schedule.start_time < sched_info['end_time'],
                    Schedule.end_time > sched_info['start_time'],
                    Schedule.teacher_id == data.teacher_id,
                    Schedule.status != 'cancelled',
                ).limit(1)
                result = await self.db.execute(teacher_conflict_query)
                if result.first():
                    has_conflict = True

            # 检测教室冲突
            if not has_conflict and data.classroom_id:
                classroom_conflict_query = select(Schedule.id).where(
                    Schedule.schedule_date == sched_info['schedule_date'],
                    Schedule.start_time < sched_info['end_time'],
                    Schedule.end_time > sched_info['start_time'],
                    Schedule.classroom_id == data.classroom_id,
                    Schedule.status != 'cancelled',
                ).limit(1)
                result = await self.db.execute(classroom_conflict_query)
                if result.first():
                    has_conflict = True

            if has_conflict:
                skipped_count += 1
                continue

            # 创建排课
            schedule = Schedule(
                class_plan_id=data.class_plan_id,
                campus_id=class_plan.campus_id,
                batch_no=batch_no,
                teacher_id=data.teacher_id,
                classroom_id=data.classroom_id,
                schedule_date=sched_info['schedule_date'],
                start_time=sched_info['start_time'],
                end_time=sched_info['end_time'],
                lesson_hours=data.lesson_hours,
                title=data.title,
                notes=data.notes,
                created_by=created_by,
                updated_by=created_by,
            )
            self.db.add(schedule)
            created_schedules.append(schedule)

        await self.db.flush()

        # Refresh all schedules to get IDs
        for schedule in created_schedules:
            await self.db.refresh(schedule)

        # Load relationships for response (only for first 50 to avoid huge queries)
        loaded_schedules: List[Schedule] = []
        for schedule in created_schedules[:50]:
            loaded = await self.get_schedule_by_id(schedule.id)
            loaded_schedules.append(loaded)

        return loaded_schedules, len(created_schedules), skipped_count, batch_no

    async def check_conflicts(self, data: ConflictCheckRequest) -> ConflictCheckResponse:
        """
        检测排课冲突：
        1. 无学生冲突 - 班级没有在读学生不能排课
        2. 教师冲突 - 同一教师同一时段不能有两个排课
        3. 教室冲突 - 同一教室同一时段不能有两个排课

        时间重叠判断：两个时间段[A_start, A_end]和[B_start, B_end]重叠的条件是：
        A_start < B_end AND A_end > B_start
        """
        conflicts: List[ConflictDetail] = []

        # 检查班级是否有在读学生（没人报名的班级排个毛课）
        active_enrollment_count = (await self.db.execute(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.class_plan_id == data.class_plan_id,
                Enrollment.status == "active"
            )
        )).scalar() or 0

        if active_enrollment_count == 0:
            # 获取班级名称
            class_plan = await self.db.get(ClassPlan, data.class_plan_id)
            class_plan_name = class_plan.name if class_plan else f"班级#{data.class_plan_id}"
            conflicts.append(ConflictDetail(
                type="no_students",
                schedule_id=0,
                class_plan_name=class_plan_name,
                schedule_date=data.schedule_date,
                start_time=data.start_time,
                end_time=data.end_time,
                message=f"班级【{class_plan_name}】没有在读学生，无法排课"
            ))

        # 基础查询条件：同一天且时间有重叠
        base_conditions = [
            Schedule.schedule_date == data.schedule_date,
            Schedule.start_time < data.end_time,
            Schedule.end_time > data.start_time,
            Schedule.status != 'cancelled',  # 排除已取消的排课
        ]

        # 如果是编辑模式，排除自己
        if data.exclude_schedule_id:
            base_conditions.append(Schedule.id != data.exclude_schedule_id)

        # 检测教师冲突
        if data.teacher_id:
            query = (
                select(Schedule)
                .options(selectinload(Schedule.class_plan))
                .where(*base_conditions, Schedule.teacher_id == data.teacher_id)
            )
            result = await self.db.execute(query)
            teacher_conflicts = result.scalars().all()

            # 获取教师名称
            teacher = await self.db.get(Teacher, data.teacher_id)
            teacher_name = teacher.name if teacher else f"教师#{data.teacher_id}"

            for schedule in teacher_conflicts:
                conflicts.append(ConflictDetail(
                    type="teacher",
                    schedule_id=schedule.id,
                    class_plan_name=schedule.class_plan.name if schedule.class_plan else "未知班级",
                    schedule_date=schedule.schedule_date,
                    start_time=schedule.start_time,
                    end_time=schedule.end_time,
                    message=f"教师【{teacher_name}】在该时段已有排课：{schedule.class_plan.name if schedule.class_plan else '未知班级'}"
                ))

        # 检测教室冲突
        if data.classroom_id:
            query = (
                select(Schedule)
                .options(selectinload(Schedule.class_plan))
                .where(*base_conditions, Schedule.classroom_id == data.classroom_id)
            )
            result = await self.db.execute(query)
            classroom_conflicts = result.scalars().all()

            # 获取教室名称
            classroom = await self.db.get(Classroom, data.classroom_id)
            classroom_name = classroom.name if classroom else f"教室#{data.classroom_id}"

            for schedule in classroom_conflicts:
                # 避免重复添加（如果同一排课既教师冲突又教室冲突）
                if not any(c.schedule_id == schedule.id and c.type == "classroom" for c in conflicts):
                    conflicts.append(ConflictDetail(
                        type="classroom",
                        schedule_id=schedule.id,
                        class_plan_name=schedule.class_plan.name if schedule.class_plan else "未知班级",
                        schedule_date=schedule.schedule_date,
                        start_time=schedule.start_time,
                        end_time=schedule.end_time,
                        message=f"教室【{classroom_name}】在该时段已被占用：{schedule.class_plan.name if schedule.class_plan else '未知班级'}"
                    ))

        return ConflictCheckResponse(
            has_conflict=len(conflicts) > 0,
            conflicts=conflicts
        )
