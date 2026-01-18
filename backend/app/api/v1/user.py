"""
User management API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DBSession
from app.models.user import User
from app.schemas.auth import PasswordResetRequest
from app.schemas.common import success_response, MessageResponse
from app.schemas.user import (
    LoginLogResponse,
    LoginLogWithUserResponse,
    OnlineUserResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户管理"])


def user_to_response(user: User) -> UserResponse:
    """
    Convert User model to UserResponse with relationship fields.
    因为Pydantic的model_validate不会自动映射关联对象的字段，
    所以这个SB转换函数手动处理role_code、role_name、campus_name。
    """
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role,
        role_id=user.role_id,
        role_code=user.user_role.code if user.user_role else None,
        role_name=user.user_role.name if user.user_role else None,
        campus_id=user.campus_id,
        campus_name=user.campus.name if user.campus else None,
        is_active=user.is_active,
        is_online=user.is_online,
        last_login=user.last_login,
        avatar=user.avatar,
        created_time=user.created_time,
        updated_time=user.updated_time,
    )


@router.get("", summary="获取用户列表")
async def get_users(
    admin_user: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    is_online: Optional[bool] = Query(None, description="是否在线筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
):
    """
    Get paginated list of users (admin only).
    """
    user_service = UserService(db)
    users, total = await user_service.get_users(
        page=page,
        page_size=page_size,
        role=role,
        is_active=is_active,
        is_online=is_online,
        search=search,
    )
    return success_response([user_to_response(u).model_dump() for u in users], total=total, page=page, page_size=page_size)


@router.post("", summary="创建用户")
async def create_user(
    user_data: UserCreate,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Create a new user (admin only).
    """
    user_service = UserService(db)
    user = await user_service.create_user(user_data, created_by=admin_user.username)
    return success_response(user_to_response(user).model_dump())


@router.get("/online", summary="获取在线用户")
async def get_online_users(
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Get list of online users (admin only).
    """
    user_service = UserService(db)
    users = await user_service.get_online_users()
    return success_response([OnlineUserResponse.model_validate(u).model_dump() for u in users])


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Get user by ID (admin only).
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    return success_response(user_to_response(user).model_dump())


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Update user information (admin only).
    """
    user_service = UserService(db)
    user = await user_service.update_user(
        user_id=user_id,
        user_data=user_data,
        updated_by=admin_user.username,
    )
    return success_response(user_to_response(user).model_dump())


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Delete a user (admin only).
    """
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return success_response({"message": "用户删除成功"})


@router.post("/{user_id}/reset-password", summary="重置密码")
async def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Reset user's password (admin only).
    """
    user_service = UserService(db)
    await user_service.reset_password(
        user_id=user_id,
        new_password=password_data.new_password,
        updated_by=admin_user.username,
    )
    return success_response({"message": "密码重置成功"})


@router.get(
    "/{user_id}/login-logs",
    summary="获取用户登录日志"
)
async def get_user_login_logs(
    user_id: int,
    admin_user: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    Get user's login logs (admin only).
    """
    user_service = UserService(db)
    logs, total = await user_service.get_login_logs(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return success_response([LoginLogResponse.model_validate(log).model_dump() for log in logs], total=total, page=page, page_size=page_size)


# Global login logs router (separate from /users)
login_logs_router = APIRouter(prefix="/login-logs", tags=["登录日志"])


@login_logs_router.get(
    "",
    summary="获取所有登录日志"
)
async def get_all_login_logs(
    admin_user: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选 (success/failed)"),
    search: Optional[str] = Query(None, description="搜索关键词 (用户名/IP)"),
):
    """
    Get all login logs with filters (admin only).
    """
    user_service = UserService(db)
    logs, total = await user_service.get_all_login_logs(
        page=page,
        page_size=page_size,
        user_id=user_id,
        status=status,
        search=search,
    )
    return success_response([LoginLogWithUserResponse.from_orm_with_user(log).model_dump() for log in logs], total=total, page=page, page_size=page_size)
