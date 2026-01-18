"""
StudentAttendance schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StudentAttendanceBase(BaseModel):
    """Base schema for student attendance."""
    status: str = Field("normal", description="出勤状态: normal/leave/absent")
    leave_reason: Optional[str] = Field(None, description="请假原因")
    deduct_hours: bool = Field(False, description="是否扣课时")
    notes: Optional[str] = Field(None, description="备注")


class StudentAttendanceCreate(StudentAttendanceBase):
    """Schema for creating attendance record."""
    enrollment_id: int = Field(..., description="报名记录ID")
    schedule_id: int = Field(..., description="排课ID")


class StudentAttendanceUpdate(BaseModel):
    """Schema for updating attendance record."""
    status: Optional[str] = Field(None, description="出勤状态: normal/leave/absent")
    leave_reason: Optional[str] = Field(None, description="请假原因")
    deduct_hours: Optional[bool] = Field(None, description="是否扣课时")
    notes: Optional[str] = Field(None, description="备注")


class StudentAttendanceResponse(StudentAttendanceBase):
    """Schema for attendance response."""
    id: int
    enrollment_id: int
    schedule_id: int
    apply_time: Optional[datetime]

    model_config = {"from_attributes": True}


class StudentAttendanceDetailResponse(StudentAttendanceResponse):
    """Detailed attendance response with related info."""
    student_name: Optional[str] = None
    schedule_date: Optional[str] = None
    class_plan_name: Optional[str] = None


class LeaveApplicationCreate(BaseModel):
    """Schema for student applying for leave."""
    schedule_id: int = Field(..., description="排课ID")
    leave_reason: str = Field(..., min_length=1, description="请假原因")


class AttendanceMarkRequest(BaseModel):
    """Schema for marking attendance (admin use)."""
    enrollment_id: int = Field(..., description="报名记录ID")
    schedule_id: int = Field(..., description="排课ID")
    status: str = Field(..., description="出勤状态: normal/leave/absent")
    leave_reason: Optional[str] = Field(None, description="请假原因")
    deduct_hours: bool = Field(False, description="是否扣课时")
    notes: Optional[str] = Field(None, description="备注")
