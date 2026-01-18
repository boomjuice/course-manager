"""
Class plan schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class CourseBriefInfo(BaseModel):
    """Brief course info for enrollment reference."""
    id: int
    name: str
    unit_price: Decimal = Field(default=Decimal("0.00"), description="课时单价")

    model_config = {"from_attributes": True}


class ClassPlanBase(BaseModel):
    """Base schema for class plan."""
    name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    course_id: int = Field(..., description="课程产品ID")
    teacher_id: Optional[int] = Field(None, description="主讲教师ID")
    campus_id: Optional[int] = Field(None, description="上课校区ID")
    classroom_id: Optional[int] = Field(None, description="默认教室ID")
    start_date: Optional[date] = Field(None, description="开班日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    max_students: int = Field(20, ge=1, le=500, description="最大人数")
    total_lessons: float = Field(0.0, ge=0, description="总课次（支持小数课时）")
    status: str = Field("pending", max_length=20, description="状态")
    description: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(True, description="是否启用")


class ClassPlanCreate(ClassPlanBase):
    """Schema for creating class plan."""
    pass


class ClassPlanUpdate(BaseModel):
    """Schema for updating class plan."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    course_id: Optional[int] = None
    teacher_id: Optional[int] = None
    campus_id: Optional[int] = None
    classroom_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_students: Optional[int] = Field(None, ge=1, le=500)
    total_lessons: Optional[float] = Field(None, ge=0, description="总课次（支持小数课时）")
    status: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ClassPlanResponse(ClassPlanBase):
    """Schema for class plan response."""
    id: int
    current_students: int
    completed_lessons: int
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClassPlanWithDetailsResponse(ClassPlanResponse):
    """Schema for class plan with related details."""
    course_name: Optional[str] = None
    teacher_name: Optional[str] = None
    campus_name: Optional[str] = None
    classroom_name: Optional[str] = None


class ClassPlanBriefResponse(BaseModel):
    """Brief class plan response for dropdowns."""
    id: int
    name: str
    course_id: int
    teacher_id: Optional[int] = None  # 主讲教师，排课时自动带出
    classroom_id: Optional[int] = None  # 默认教室，排课时自动带出
    status: str
    current_students: int = 0  # 当前报名人数，用于教室容量校验
    course: Optional[CourseBriefInfo] = None  # 课程简要信息，用于报名时参考

    model_config = {"from_attributes": True}
