"""
Campus and Classroom schemas.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


# ============ Classroom Schemas ============

class ClassroomBase(BaseModel):
    """Base schema for classroom."""
    name: str = Field(..., min_length=1, max_length=100, description="教室名称")
    capacity: int = Field(20, ge=1, le=500, description="容纳人数")
    description: Optional[str] = Field(None, description="描述")
    equipment: Optional[Dict[str, str]] = Field(None, description="设备配置（key-value形式，如{'投影仪': '有', '白板': '2块'}）")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, ge=0, description="排序")


class ClassroomCreate(ClassroomBase):
    """Schema for creating classroom."""
    pass


class ClassroomUpdate(BaseModel):
    """Schema for updating classroom."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=500)
    description: Optional[str] = None
    equipment: Optional[Dict[str, str]] = Field(None, description="设备配置（key-value形式）")
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class ClassroomResponse(ClassroomBase):
    """Schema for classroom response."""
    id: int
    campus_id: int
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClassroomWithCampusResponse(ClassroomResponse):
    """Schema for classroom with campus name."""
    campus_name: Optional[str] = None


# ============ Campus Schemas ============

class CampusBase(BaseModel):
    """Base schema for campus."""
    name: str = Field(..., min_length=1, max_length=100, description="校区名称")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, ge=0, description="排序")


class CampusCreate(CampusBase):
    """Schema for creating campus with optional classrooms."""
    classrooms: Optional[List[ClassroomCreate]] = Field(None, description="教室列表")


class CampusUpdate(BaseModel):
    """Schema for updating campus."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class CampusResponse(CampusBase):
    """Schema for campus response without classrooms."""
    id: int
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CampusWithClassroomsResponse(CampusResponse):
    """Schema for campus response with classrooms."""
    classrooms: List[ClassroomResponse] = []
