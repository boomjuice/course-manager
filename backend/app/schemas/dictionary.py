"""
Dictionary schemas for request/response validation.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ DictItem Schemas ============

class DictItemBase(BaseModel):
    """Base schema for dict item."""
    value: str = Field(..., min_length=1, max_length=100, description="字典值")
    label: str = Field(..., min_length=1, max_length=100, description="显示标签")
    description: Optional[str] = Field(None, description="描述")
    color: Optional[str] = Field(None, max_length=20, description="显示颜色")
    is_default: bool = Field(False, description="是否默认值")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, ge=0, description="排序")


class DictItemCreate(DictItemBase):
    """Schema for creating dict item."""
    pass


class DictItemUpdate(BaseModel):
    """Schema for updating dict item."""
    value: Optional[str] = Field(None, min_length=1, max_length=100)
    label: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class DictItemResponse(DictItemBase):
    """Schema for dict item response."""
    id: int
    type_id: int

    model_config = {"from_attributes": True}


# ============ DictType Schemas ============

class DictTypeBase(BaseModel):
    """Base schema for dict type."""
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$", description="字典类型编码")
    name: str = Field(..., min_length=1, max_length=100, description="字典类型名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, ge=0, description="排序")


class DictTypeCreate(DictTypeBase):
    """Schema for creating dict type with optional items."""
    items: Optional[List[DictItemCreate]] = Field(None, description="字典项列表")


class DictTypeUpdate(BaseModel):
    """Schema for updating dict type."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class DictTypeResponse(DictTypeBase):
    """Schema for dict type response without items."""
    id: int
    is_system: bool

    model_config = {"from_attributes": True}


class DictTypeWithItemsResponse(DictTypeResponse):
    """Schema for dict type response with items."""
    items: List[DictItemResponse] = []


# ============ Batch Operations ============

class DictItemBatchCreate(BaseModel):
    """Schema for batch creating dict items."""
    items: List[DictItemCreate] = Field(..., min_length=1, description="字典项列表")


class DictItemBatchUpdate(BaseModel):
    """Schema for batch updating dict items order."""
    item_ids: List[int] = Field(..., min_length=1, description="按顺序排列的字典项ID列表")
