"""
Teacher schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class TeacherBase(BaseModel):
    """Base schema for teacher."""
    name: str = Field(..., min_length=1, max_length=50, description="教师姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    phone: str = Field(..., min_length=11, max_length=20, description="联系电话（必填，用于创建登录账号）")
    email: Optional[str] = Field(None, max_length=100, description="电子邮箱")
    id_card: Optional[str] = Field(None, max_length=20, description="身份证号")
    entry_date: Optional[date] = Field(None, description="入职日期")
    education: Optional[str] = Field(None, max_length=50, description="学历")
    major: Optional[str] = Field(None, max_length=100, description="专业")
    subjects: Optional[List[str]] = Field(None, description="负责科目（字典值数组）")
    grade_levels: Optional[List[str]] = Field(None, description="负责年级（字典值数组）")
    hourly_rate: Decimal = Field(Decimal("0.00"), ge=0, description="课时费单价")
    introduction: Optional[str] = Field(None, description="简介")
    status: str = Field("active", max_length=20, description="状态")
    is_active: bool = Field(True, description="是否启用")


class TeacherCreate(TeacherBase):
    """Schema for creating teacher."""
    user_id: Optional[int] = Field(None, description="关联用户账号ID")


class TeacherUpdate(BaseModel):
    """Schema for updating teacher."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    id_card: Optional[str] = Field(None, max_length=20)
    entry_date: Optional[date] = None
    education: Optional[str] = Field(None, max_length=50)
    major: Optional[str] = Field(None, max_length=100)
    subjects: Optional[List[str]] = None
    grade_levels: Optional[List[str]] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    introduction: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    user_id: Optional[int] = None


class TeacherResponse(TeacherBase):
    """Schema for teacher response."""
    id: int
    user_id: Optional[int]
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TeacherBriefResponse(BaseModel):
    """Brief teacher response for dropdowns."""
    id: int
    name: str
    phone: Optional[str] = None
    subjects: Optional[List[str]] = None
    grade_levels: Optional[List[str]] = None
    status: str

    model_config = {"from_attributes": True}
