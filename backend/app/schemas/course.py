"""
Course product schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class CourseBase(BaseModel):
    """Base schema for course."""
    name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    code: Optional[str] = Field(None, max_length=50, description="课程编码")
    subject: Optional[str] = Field(None, max_length=50, description="学科")
    grade_level: Optional[str] = Field(None, max_length=20, description="年级")
    level: Optional[str] = Field(None, max_length=50, description="难度级别")
    unit_price: Decimal = Field(Decimal("0.00"), ge=0, description="课时单价（开班时可修改）")
    description: Optional[str] = Field(None, description="课程描述")
    objectives: Optional[str] = Field(None, description="学习目标")
    target_audience: Optional[str] = Field(None, max_length=200, description="适合人群")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, ge=0, description="排序")


class CourseCreate(CourseBase):
    """Schema for creating course."""
    campus_id: Optional[int] = Field(None, description="所属校区ID")


class CourseUpdate(BaseModel):
    """Schema for updating course."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    subject: Optional[str] = Field(None, max_length=50)
    grade_level: Optional[str] = Field(None, max_length=20)
    level: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[Decimal] = Field(None, ge=0, description="课时单价")
    description: Optional[str] = None
    objectives: Optional[str] = None
    target_audience: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class CourseResponse(CourseBase):
    """Schema for course response."""
    id: int
    campus_id: Optional[int] = None
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
