"""
Schedule related Pydantic schemas.
"""
from datetime import date, time, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScheduleBase(BaseModel):
    """Base schedule schema."""
    class_plan_id: int = Field(..., description="班级计划ID")
    teacher_id: Optional[int] = Field(None, description="授课教师ID")
    classroom_id: Optional[int] = Field(None, description="教室ID")
    schedule_date: date = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    lesson_hours: float = Field(default=2.0, ge=0.1, le=24, description="课时数（支持小数，如1.5课时）")
    title: Optional[str] = Field(None, max_length=200, description="课程标题")
    notes: Optional[str] = Field(None, description="备注")


class ScheduleCreate(ScheduleBase):
    """Schema for creating a schedule."""
    pass


class TimeSlot(BaseModel):
    """时间段配置，支持不同的周几使用不同的上课时间"""
    weekdays: List[int] = Field(..., description="每周几上课，0=周一，6=周日", min_length=1)
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")


class DateRange(BaseModel):
    """日期范围"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")


class ScheduleBatchCreate(BaseModel):
    """Schema for batch creating schedules (periodic scheduling).

    支持周期性批量排课，可以配置多个时间段和多个日期范围。
    例如：
    - 日期范围：1月5日-1月20日（寒假班）、2月15日-2月28日（开学前）
    - 时间段：周一三五上午9-11点、周二四下午2-4点
    """
    class_plan_id: int = Field(..., description="班级计划ID")
    teacher_id: Optional[int] = Field(None, description="授课教师ID")
    classroom_id: Optional[int] = Field(None, description="教室ID")
    date_ranges: List[DateRange] = Field(..., description="日期范围列表", min_length=1)
    time_slots: List[TimeSlot] = Field(..., description="时间段配置列表", min_length=1)
    lesson_hours: float = Field(default=2.0, ge=0.1, le=24, description="每次课时数（支持小数，如1.5课时）")
    title: Optional[str] = Field(None, max_length=200, description="课程标题")
    notes: Optional[str] = Field(None, description="备注")
    max_count: Optional[int] = Field(None, ge=1, description="最大创建数量（用于课时限制场景）")


class ScheduleBatchResponse(BaseModel):
    """Response for batch schedule creation."""
    created_count: int = Field(..., description="成功创建的排课数量")
    skipped_count: int = Field(default=0, description="跳过的数量（如冲突）")
    batch_no: Optional[str] = Field(None, description="批次号，可用于后续批量操作")
    schedules: List["ScheduleResponse"] = Field(default_factory=list, description="创建的排课列表")


class BatchConflictItem(BaseModel):
    """批量创建时的单条冲突信息"""
    schedule_date: date
    start_time: time
    end_time: time
    conflict_type: str = Field(..., description="冲突类型: teacher/classroom")
    conflict_with: str = Field(..., description="冲突的对象描述，如'教师张三已有排课：初级班'")


class ScheduleBatchPreviewResponse(BaseModel):
    """批量创建预检测响应"""
    total_count: int = Field(..., description="计划创建的总数量")
    conflict_count: int = Field(..., description="有冲突的数量")
    conflicts: List[BatchConflictItem] = Field(default_factory=list, description="冲突详情列表")


class ScheduleBatchUpdate(BaseModel):
    """Schema for batch updating schedules.

    用于批量更新选中的排课。
    典型场景：这个批次7天课，用户勾选后3天要换老师。
    """
    schedule_ids: List[int] = Field(..., min_length=1, description="要更新的排课ID列表")
    teacher_id: Optional[int] = Field(None, description="新的授课教师ID（不传则不更新）")
    classroom_id: Optional[int] = Field(None, description="新的教室ID（不传则不更新）")
    notes: Optional[str] = Field(None, description="备注（不传则不更新）")


class ScheduleBatchUpdateResponse(BaseModel):
    """Response for batch update operation."""
    updated_count: int = Field(..., description="成功更新的排课数量")
    message: str = Field(..., description="操作结果消息")


class ScheduleBatchDeleteRequest(BaseModel):
    """Schema for batch deleting schedules by IDs."""
    schedule_ids: List[int] = Field(..., min_length=1, description="要删除的排课ID列表")


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule."""
    teacher_id: Optional[int] = Field(None, description="授课教师ID")
    classroom_id: Optional[int] = Field(None, description="教室ID")
    schedule_date: Optional[date] = Field(None, description="上课日期")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    lesson_hours: Optional[float] = Field(None, ge=0.1, le=24, description="课时数（支持小数）")
    title: Optional[str] = Field(None, max_length=200, description="课程标题")
    status: Optional[str] = Field(None, description="状态")
    notes: Optional[str] = Field(None, description="备注")


class ClassPlanBrief(BaseModel):
    """Brief class plan info for schedule response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class TeacherBrief(BaseModel):
    """Brief teacher info."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ClassroomBrief(BaseModel):
    """Brief classroom info."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ScheduleResponse(BaseModel):
    """Schema for schedule response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_plan_id: int
    campus_id: Optional[int] = None
    batch_no: Optional[str] = None
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
    schedule_date: date
    start_time: time
    end_time: time
    lesson_hours: float
    title: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_time: datetime
    updated_time: Optional[datetime] = None
    class_plan: Optional[ClassPlanBrief] = None
    teacher: Optional[TeacherBrief] = None
    classroom: Optional[ClassroomBrief] = None


class ScheduleListResponse(BaseModel):
    """Schema for paginated schedule list response."""
    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    page_size: int
    items: List[ScheduleResponse]


class CalendarEventResponse(BaseModel):
    """Schema for TOAST UI Calendar event format."""
    id: str
    calendarId: str
    title: str
    category: str = "time"
    start: str  # ISO format
    end: str  # ISO format
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    state: Optional[str] = None
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    raw: Optional[dict] = None


# 冲突检测相关
class ConflictDetail(BaseModel):
    """冲突详情"""
    type: str = Field(..., description="冲突类型: teacher/classroom")
    schedule_id: int = Field(..., description="冲突的排课ID")
    class_plan_name: str = Field(..., description="冲突的班级名称")
    schedule_date: date
    start_time: time
    end_time: time
    message: str = Field(..., description="冲突描述")


class ConflictCheckRequest(BaseModel):
    """冲突检测请求"""
    class_plan_id: int = Field(..., description="班级ID")
    teacher_id: Optional[int] = Field(None, description="教师ID")
    classroom_id: Optional[int] = Field(None, description="教室ID")
    schedule_date: date = Field(..., description="上课日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    exclude_schedule_id: Optional[int] = Field(None, description="排除的排课ID（编辑时使用）")


class ConflictCheckResponse(BaseModel):
    """冲突检测响应"""
    has_conflict: bool = Field(..., description="是否有冲突")
    conflicts: List[ConflictDetail] = Field(default_factory=list, description="冲突列表")
