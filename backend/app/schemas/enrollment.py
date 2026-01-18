"""
Enrollment related Pydantic schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentBrief(BaseModel):
    """Brief student info for enrollment response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: Optional[str] = None


class ClassPlanBrief(BaseModel):
    """Brief class plan info for enrollment response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class EnrollmentCreate(BaseModel):
    """Schema for creating an enrollment."""
    student_id: int = Field(..., description="学生ID")
    class_plan_id: int = Field(..., description="班级计划ID")
    paid_amount: Decimal = Field(default=Decimal("0.00"), description="付款金额")
    purchased_hours: Decimal = Field(default=Decimal("0.0"), description="购买课时")
    status: str = Field(default="active", description="状态")
    notes: Optional[str] = Field(None, description="备注")


class EnrollmentUpdate(BaseModel):
    """Schema for updating an enrollment."""
    paid_amount: Optional[Decimal] = Field(None, description="付款金额")
    purchased_hours: Optional[Decimal] = Field(None, description="购买课时")
    used_hours: Optional[Decimal] = Field(None, description="已使用课时")
    status: Optional[str] = Field(None, description="状态")
    notes: Optional[str] = Field(None, description="备注")


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    class_plan_id: int
    enroll_date: Optional[date] = None
    paid_amount: Decimal
    purchased_hours: Decimal
    used_hours: Decimal
    scheduled_hours: Decimal = Field(default=Decimal("0.0"), description="已排课时总数")
    status: str
    notes: Optional[str] = None
    created_time: datetime
    updated_time: Optional[datetime] = None
    student: Optional[StudentBrief] = None
    class_plan: Optional[ClassPlanBrief] = None
