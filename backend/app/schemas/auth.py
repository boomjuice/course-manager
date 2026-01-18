"""
Authentication related Pydantic schemas.
"""
from typing import Optional, List

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class CampusOption(BaseModel):
    """Campus option for selection."""

    id: int = Field(..., description="校区ID")
    name: str = Field(..., description="校区名称")


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class LoginResponse(BaseModel):
    """Login response schema with campus selection info."""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    need_select_campus: bool = Field(default=False, description="是否需要选择校区")
    available_campuses: List[CampusOption] = Field(default_factory=list, description="可选校区列表")
    current_campus_id: Optional[int] = Field(None, description="当前选中的校区ID")


class SelectCampusRequest(BaseModel):
    """Select campus request schema."""

    campus_id: int = Field(..., description="选择的校区ID")


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="用户角色")
    role_code: Optional[str] = Field(None, description="角色编码")
    campus_id: Optional[int] = Field(None, description="当前校区ID")
    exp: int = Field(..., description="过期时间")
    type: str = Field(..., description="令牌类型")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="刷新令牌")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class PasswordResetRequest(BaseModel):
    """Admin password reset request schema."""

    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class ProfileUpdateRequest(BaseModel):
    """Profile update request schema."""

    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")
