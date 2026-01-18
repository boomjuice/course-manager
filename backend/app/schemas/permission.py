"""
Permission related schemas for RBAC.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== Resource Schemas ====================

class ResourceBase(BaseModel):
    """资源基础Schema"""
    code: str = Field(..., max_length=50, description="资源编码")
    name: str = Field(..., max_length=100, description="资源名称")
    description: Optional[str] = Field(None, description="描述")
    sort_order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")


class ResourceCreate(ResourceBase):
    """创建资源Schema"""
    pass


class ResourceUpdate(BaseModel):
    """更新资源Schema"""
    name: Optional[str] = Field(None, max_length=100, description="资源名称")
    description: Optional[str] = Field(None, description="描述")
    sort_order: Optional[int] = Field(None, description="排序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ResourceResponse(ResourceBase):
    """资源响应Schema"""
    id: int

    class Config:
        from_attributes = True


# ==================== Permission Schemas ====================

class PermissionBase(BaseModel):
    """权限基础Schema"""
    resource_id: int = Field(..., description="资源ID")
    action: str = Field(..., max_length=20, description="操作类型: read/edit/delete")
    name: str = Field(..., max_length=100, description="权限名称")
    description: Optional[str] = Field(None, description="描述")


class PermissionResponse(BaseModel):
    """权限响应Schema"""
    id: int
    resource_id: int
    action: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class ResourceWithPermissions(ResourceResponse):
    """资源及其权限响应Schema"""
    permissions: List[PermissionResponse] = []


# ==================== Role Schemas ====================

class RoleBase(BaseModel):
    """角色基础Schema"""
    code: str = Field(..., max_length=50, description="角色编码")
    name: str = Field(..., max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否启用")


class RoleCreate(RoleBase):
    """创建角色Schema"""
    permission_ids: List[int] = Field(default=[], description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色Schema"""
    name: Optional[str] = Field(None, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class RoleResponse(RoleBase):
    """角色响应Schema"""
    id: int
    is_system: bool = Field(False, description="是否系统内置角色")
    created_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class RolePermissionUpdate(BaseModel):
    """更新角色权限Schema"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class RoleWithPermissions(RoleResponse):
    """角色及其权限响应Schema"""
    permissions: List[PermissionResponse] = []


# ==================== User Permission Schemas ====================

class UserPermissionInfo(BaseModel):
    """用户权限信息Schema（登录后返回）"""
    role_code: Optional[str] = Field(None, description="角色编码")
    role_name: Optional[str] = Field(None, description="角色名称")
    campus_id: Optional[int] = Field(None, description="所属校区ID")
    campus_name: Optional[str] = Field(None, description="所属校区名称")
    permissions: List[str] = Field(default=[], description="权限列表 (格式: resource:action)")
    is_super_admin: bool = Field(False, description="是否超级管理员")
