"""
Authentication API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request

from app.api.deps import CurrentUser, DBSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    RefreshTokenRequest,
    SelectCampusRequest,
    TokenResponse,
)
from app.schemas.common import success_response, MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="用户登录")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: DBSession,
    user_agent: Optional[str] = Header(None),
):
    """
    Authenticate user and return access/refresh tokens with campus selection info.

    Response fields:
    - need_select_campus: True if user needs to select a campus before proceeding
    - available_campuses: List of campuses user can access (only when need_select_campus=True)
    - current_campus_id: Currently selected campus ID (None if need_select_campus=True)
    """
    # Get client IP
    ip_address = request.client.host if request.client else None

    auth_service = AuthService(db)
    result = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return success_response(result.model_dump())


@router.post("/select-campus", summary="选择校区")
async def select_campus(
    campus_data: SelectCampusRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Select a campus and get new tokens with campus_id embedded.

    This endpoint is called after login when need_select_campus=True.
    Teachers and super admins can access multiple campuses.
    """
    auth_service = AuthService(db)
    result = await auth_service.select_campus(
        user=current_user,
        campus_id=campus_data.campus_id,
    )
    return success_response(result.model_dump())


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Logout current user and mark as offline.
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user)
    return success_response({"message": "登出成功"})


@router.post("/refresh", summary="刷新令牌")
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: DBSession,
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    result = await auth_service.refresh_tokens(token_data.refresh_token)
    return success_response(result.model_dump())


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: CurrentUser,
):
    """
    Get current authenticated user information.
    """
    return success_response(UserResponse.model_validate(current_user).model_dump())


@router.put("/password", summary="修改密码")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Change current user's password.
    """
    auth_service = AuthService(db)
    await auth_service.change_password(
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
    )
    return success_response({"message": "密码修改成功"})


@router.put("/profile", summary="更新个人资料")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Update current user's profile (email, phone, avatar).
    """
    auth_service = AuthService(db)
    user = await auth_service.update_profile(
        user=current_user,
        email=profile_data.email,
        phone=profile_data.phone,
        avatar=profile_data.avatar,
    )
    return success_response(UserResponse.model_validate(user).model_dump())
