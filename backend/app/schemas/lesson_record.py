"""
LessonRecord schemas - 课时消耗记录
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class LessonRecordBase(BaseModel):
    """课时消耗记录基础"""
    enrollment_id: int = Field(..., description="报名记录ID")
    schedule_id: Optional[int] = Field(None, description="排课ID")
    record_date: date = Field(..., description="消耗日期")
    hours: Decimal = Field(..., description="消耗课时数")
    type: str = Field(default="schedule", description="类型")
    notes: Optional[str] = Field(None, description="备注")


class LessonRecordCreate(LessonRecordBase):
    """创建课时消耗记录"""
    pass


class LessonRecordResponse(LessonRecordBase):
    """课时消耗记录响应"""
    id: int
    created_time: datetime
    # 关联信息
    student_name: Optional[str] = None
    class_plan_name: Optional[str] = None
    teacher_name: Optional[str] = None
    schedule_date: Optional[date] = None

    model_config = {"from_attributes": True}


class LessonRecordListResponse(BaseModel):
    """课时消耗记录列表响应"""
    items: List[LessonRecordResponse]
    total: int
    page: int
    page_size: int
