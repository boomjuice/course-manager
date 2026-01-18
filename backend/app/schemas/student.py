"""
Student schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class StudentBase(BaseModel):
    """Base schema for student."""
    name: str = Field(..., min_length=1, max_length=50, description="学生姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[date] = Field(None, description="生日")
    phone: str = Field(..., min_length=11, max_length=20, description="联系电话（必填，用于创建登录账号）")
    parent_name: Optional[str] = Field(None, max_length=50, description="家长姓名")
    parent_phone: Optional[str] = Field(None, max_length=20, description="家长电话")
    school: Optional[str] = Field(None, max_length=100, description="就读学校")
    grade: Optional[str] = Field(None, max_length=50, description="年级")
    address: Optional[str] = Field(None, max_length=300, description="家庭住址")
    source: Optional[str] = Field(None, max_length=50, description="来源渠道")
    subject_levels: Optional[List[str]] = Field(None, description="科目水平标签（格式: subject:level）")
    learning_goals: Optional[List[str]] = Field(None, description="学习目标（字典值数组）")
    remark: Optional[str] = Field(None, description="备注")
    status: str = Field("active", max_length=20, description="状态")
    is_active: bool = Field(True, description="是否启用")


class StudentCreate(StudentBase):
    """Schema for creating student."""
    user_id: Optional[int] = Field(None, description="关联用户账号ID")
    campus_id: Optional[int] = Field(None, description="所属校区ID")


class StudentUpdate(BaseModel):
    """Schema for updating student."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    birthday: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=20)
    parent_name: Optional[str] = Field(None, max_length=50)
    parent_phone: Optional[str] = Field(None, max_length=20)
    school: Optional[str] = Field(None, max_length=100)
    grade: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=300)
    source: Optional[str] = Field(None, max_length=50)
    subject_levels: Optional[List[str]] = None
    learning_goals: Optional[List[str]] = None
    remark: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    user_id: Optional[int] = None


class StudentResponse(StudentBase):
    """Schema for student response."""
    id: int
    user_id: Optional[int]
    campus_id: Optional[int]
    total_hours: Decimal
    remaining_hours: Decimal
    total_paid: Decimal
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StudentBriefResponse(BaseModel):
    """Brief student response for dropdowns."""
    id: int
    name: str
    phone: Optional[str]
    status: str

    model_config = {"from_attributes": True}
