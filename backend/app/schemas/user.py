"""
User related Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    role: Role = Field(default=Role.STUDENT, description="角色(兼容旧版)")
    role_id: Optional[int] = Field(None, description="RBAC角色ID")
    campus_id: Optional[int] = Field(None, description="所属校区ID")
    is_active: bool = Field(default=True, description="是否启用")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    username: Optional[str] = Field(None, min_length=2, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    role: Optional[Role] = Field(None, description="角色(兼容旧版)")
    role_id: Optional[int] = Field(None, description="RBAC角色ID")
    campus_id: Optional[int] = Field(None, description="所属校区ID")
    is_active: Optional[bool] = Field(None, description="是否启用")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str  # 兼容旧版
    role_id: Optional[int] = None
    role_code: Optional[str] = None  # RBAC角色编码
    role_name: Optional[str] = None  # RBAC角色名称
    campus_id: Optional[int] = None
    campus_name: Optional[str] = None  # 校区名称
    is_active: bool
    is_online: bool
    last_login: Optional[datetime] = None
    avatar: Optional[str] = None
    created_time: datetime
    updated_time: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    page_size: int
    items: List[UserResponse]


class LoginLogResponse(BaseModel):
    """Schema for login log response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    login_time: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    fail_reason: Optional[str] = None


class LoginLogWithUserResponse(LoginLogResponse):
    """Schema for login log response with user info."""

    username: Optional[str] = None

    @classmethod
    def from_orm_with_user(cls, log) -> "LoginLogWithUserResponse":
        """Create from ORM object with user relationship."""
        return cls(
            id=log.id,
            user_id=log.user_id,
            login_time=log.login_time,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            status=log.status,
            fail_reason=log.fail_reason,
            username=log.user.username if log.user else None,
        )


class OnlineUserResponse(BaseModel):
    """Schema for online user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    last_login: Optional[datetime] = None
    avatar: Optional[str] = None
