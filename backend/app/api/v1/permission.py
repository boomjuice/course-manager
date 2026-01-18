"""
Permission management API endpoints.
角色权限管理接口。
"""
from typing import List

from fastapi import APIRouter, Query

from app.api.deps import (
    DBSession, CurrentUser, CampusScopedQuery,
    RolePermissionRead, RolePermissionEdit, RolePermissionDelete,
)
from app.services.permission_service import PermissionService
from app.schemas.permission import (
    RoleCreate, RoleUpdate, RoleResponse, RoleWithPermissions,
    ResourceWithPermissions, RolePermissionUpdate, UserPermissionInfo
)
from app.schemas.common import success_response, MessageResponse

router = APIRouter(prefix="/permissions", tags=["角色权限管理"])


@router.get("/resources", summary="获取所有资源模块")
async def get_resources(
    current_user: RolePermissionRead,
    db: DBSession,
):
    """
    获取所有系统资源模块及其权限。
    用于角色权限配置页面。
    """
    service = PermissionService(db)
    return success_response(await service.get_all_resources())


@router.get("/roles", summary="获取角色列表")
async def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: RolePermissionRead = None,
    db: DBSession = None,
):
    """获取角色列表（分页）"""
    service = PermissionService(db)
    items, total = await service.get_roles(page, page_size)
    # UserRole 是 SQLAlchemy 模型，用 RoleResponse 转换
    return success_response({
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [RoleResponse.model_validate(item).model_dump() for item in items]
    })


@router.get("/roles/{role_id}", summary="获取角色详情")
async def get_role(
    role_id: int,
    current_user: RolePermissionRead = None,
    db: DBSession = None,
):
    """获取角色及其权限详情"""
    service = PermissionService(db)
    return success_response((await service.get_role_with_permissions(role_id)).model_dump())


@router.post("/roles", summary="创建角色")
async def create_role(
    data: RoleCreate,
    current_user: RolePermissionEdit = None,
    db: DBSession = None,
):
    """创建新角色"""
    service = PermissionService(db)
    role = await service.create_role(data, current_user.username)
    return success_response(RoleResponse.model_validate(role).model_dump())


@router.put("/roles/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    current_user: RolePermissionEdit = None,
    db: DBSession = None,
):
    """更新角色信息"""
    service = PermissionService(db)
    role = await service.update_role(role_id, data, current_user.username)
    return success_response(RoleResponse.model_validate(role).model_dump())


@router.put("/roles/{role_id}/permissions", summary="更新角色权限")
async def update_role_permissions(
    role_id: int,
    data: RolePermissionUpdate,
    current_user: RolePermissionEdit = None,
    db: DBSession = None,
):
    """更新角色的权限配置"""
    service = PermissionService(db)
    await service.update_role_permissions(role_id, data.permission_ids)
    return success_response(MessageResponse(message="权限更新成功").model_dump())


@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: RolePermissionDelete = None,
    db: DBSession = None,
):
    """删除角色（系统内置角色不可删除）"""
    service = PermissionService(db)
    await service.delete_role(role_id)
    return success_response(MessageResponse(message="删除成功").model_dump())


@router.get("/current", summary="获取当前用户权限")
async def get_current_user_permissions(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    获取当前用户的权限信息。
    登录后调用此接口获取用户权限列表。
    """
    service = PermissionService(db)
    scope = CampusScopedQuery()

    # 判断是否超级管理员
    is_super_admin = scope.is_super_admin(current_user)

    # 获取权限列表
    permissions: List[str] = []
    if is_super_admin:
        # 超级管理员拥有所有权限
        all_permissions = await service.get_all_permissions()
        resources = await service.get_all_resources()
        for res in resources:
            for perm in res.permissions:
                permissions.append(f"{res.code}:{perm.action}")
    elif current_user.role_id:
        permissions = await service.get_permissions_by_role_id(current_user.role_id)

    # 获取角色信息
    role_code = None
    role_name = None
    if current_user.user_role:
        role_code = current_user.user_role.code
        role_name = current_user.user_role.name

    # 获取校区信息
    campus_name = None
    if current_user.campus:
        campus_name = current_user.campus.name

    return success_response(UserPermissionInfo(
        role_code=role_code,
        role_name=role_name,
        campus_id=current_user.campus_id,
        campus_name=campus_name,
        permissions=permissions,
        is_super_admin=is_super_admin
    ).model_dump())
