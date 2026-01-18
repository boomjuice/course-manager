"""
API dependencies for authentication, RBAC permission check and campus scope filter.
核心权限检查模块，支持：
1. JWT Token验证
2. RBAC权限检查（资源:操作 粒度）
3. 校区数据范围过滤
"""
from typing import Annotated, Optional, Set

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import verify_token
from app.database import get_db
from app.models.user import Role, User
from app.models.permission import UserRole, RolePermission, Permission, Resource


# 权限缓存（简单内存缓存，生产环境可用Redis）
_permission_cache: dict[int, Set[str]] = {}


def clear_permission_cache(user_id: int = None):
    """
    清除权限缓存。
    角色权限变更后需要调用此函数。
    """
    global _permission_cache
    if user_id:
        _permission_cache.pop(user_id, None)
    else:
        _permission_cache = {}


async def get_user_permissions(db: AsyncSession, user_id: int, role_id: int) -> Set[str]:
    """
    获取用户所有权限（格式：resource_code:action）。
    结果会被缓存。
    """
    cache_key = user_id
    if cache_key in _permission_cache:
        return _permission_cache[cache_key]

    result = await db.execute(
        select(Resource.code, Permission.action)
        .join(Permission, Permission.resource_id == Resource.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )

    permissions = {f"{row.code}:{row.action}" for row in result}
    _permission_cache[cache_key] = permissions
    return permissions


class TokenCampusInfo:
    """
    Store campus_id from JWT token.
    This is attached to User object during authentication.
    """
    campus_id: Optional[int] = None
    role_code: Optional[str] = None


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    加载用户的同时预加载角色信息，并从JWT中提取campus_id。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("未提供认证令牌")

    token = authorization.split(" ")[1]
    payload = verify_token(token, token_type="access")

    if not payload:
        raise UnauthorizedException("无效的认证令牌")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("无效的认证令牌")

    result = await db.execute(
        select(User)
        .options(selectinload(User.user_role), selectinload(User.campus))
        .where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("用户不存在")

    if not user.is_active:
        raise UnauthorizedException("用户已被禁用")

    # Attach JWT campus_id to user object for data filtering
    # This is the campus selected at login, not from database
    user._token_campus_id = payload.get("campus_id")
    user._token_role_code = payload.get("role_code")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise UnauthorizedException("用户已被禁用")
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they are a super admin.
    兼容旧版role字段和新版role_id。
    """
    # 新版RBAC检查
    if current_user.user_role and current_user.user_role.code == "super_admin":
        return current_user
    # 兼容旧版
    if current_user.role == Role.ADMIN.value:
        return current_user
    raise ForbiddenException("需要超级管理员权限")


class RoleChecker:
    """
    Role-based permission checker (兼容旧版)。

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(RoleChecker([Role.ADMIN]))):
            ...
    """

    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = [r.value for r in allowed_roles]

    async def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(
                f"需要以下角色之一: {', '.join(self.allowed_roles)}"
            )
        return current_user


class PermissionChecker:
    """
    RBAC权限检查器。
    检查用户是否拥有指定资源的指定操作权限。

    Usage:
        @router.get("/students")
        async def get_students(
            user: User = Depends(PermissionChecker("student", "read"))
        ):
            ...
    """

    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action
        self.required_permission = f"{resource}:{action}"

    async def __call__(
        self,
        db: AsyncSession = Depends(get_db),
        authorization: Annotated[Optional[str], Header()] = None,
    ) -> User:
        # 1. 验证Token获取用户
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedException("未提供认证令牌")

        token = authorization.split(" ")[1]
        payload = verify_token(token, token_type="access")

        if not payload:
            raise UnauthorizedException("无效的认证令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("无效的认证令牌")

        # 2. 获取用户及角色和校区
        result = await db.execute(
            select(User)
            .options(selectinload(User.user_role), selectinload(User.campus))
            .where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedException("用户不存在")
        if not user.is_active:
            raise UnauthorizedException("用户已被禁用")

        # 3. 从JWT中提取campus_id和role_code，附加到用户对象
        user._token_campus_id = payload.get("campus_id")
        user._token_role_code = payload.get("role_code")

        # 4. 超级管理员跳过权限检查
        if user.user_role and user.user_role.code == "super_admin":
            return user
        # 兼容旧版admin角色
        if user.role == Role.ADMIN.value and not user.role_id:
            return user

        # 5. 检查RBAC权限
        if not user.role_id:
            raise ForbiddenException("用户未分配角色")

        permissions = await get_user_permissions(db, user.id, user.role_id)
        if self.required_permission not in permissions:
            raise ForbiddenException(
                f"无权限访问此资源 (需要: {self.required_permission})"
            )

        return user


class CampusScopedQuery:
    """
    校区数据范围过滤器。
    从JWT token中读取campus_id进行数据过滤。

    Usage:
        scope = CampusScopedQuery()
        campus_id = scope.get_campus_filter(user)
        if campus_id:
            query = query.where(Model.campus_id == campus_id)
    """

    def get_campus_filter(self, user: User) -> Optional[int]:
        """
        获取用户的校区过滤ID（从JWT token读取）。
        - 未选择校区时: 返回None（无法访问业务数据）
        - 已选择校区时: 返回选中的campus_id
        """
        # 从JWT中获取campus_id
        token_campus_id = getattr(user, '_token_campus_id', None)
        return token_campus_id

    def get_token_role_code(self, user: User) -> Optional[str]:
        """获取JWT中的角色编码"""
        return getattr(user, '_token_role_code', None)

    def is_teacher(self, user: User) -> bool:
        """判断是否是教师角色"""
        token_role_code = getattr(user, '_token_role_code', None)
        if token_role_code == "teacher":
            return True
        if user.user_role and user.user_role.code == "teacher":
            return True
        return False

    def is_super_admin(self, user: User) -> bool:
        """判断是否是超级管理员"""
        token_role_code = getattr(user, '_token_role_code', None)
        if token_role_code == "super_admin":
            return True
        if user.user_role and user.user_role.code == "super_admin":
            return True
        # 兼容旧版
        if user.role == Role.ADMIN.value and not user.role_id:
            return True
        return False

    def has_campus_selected(self, user: User) -> bool:
        """判断用户是否已选择校区"""
        token_campus_id = getattr(user, '_token_campus_id', None)
        return token_campus_id is not None

    def require_campus_for_business(self, user: User) -> Optional[int]:
        """
        要求用户必须已选择校区才能访问业务数据。
        超级管理员可以不选择校区访问全部数据。
        """
        if self.is_super_admin(user):
            # 超管已选择校区时按校区过滤，未选择时返回None（全部数据）
            return getattr(user, '_token_campus_id', None)
        # 非超管必须有校区
        token_campus_id = getattr(user, '_token_campus_id', None)
        if token_campus_id is None:
            raise ForbiddenException("请先选择校区")
        return token_campus_id

    async def get_teacher_id_for_user(self, db: AsyncSession, user: User) -> Optional[int]:
        """
        获取用户对应的教师ID（仅教师角色有效）。
        通过 Teacher.user_id 关联查询。
        """
        if not self.is_teacher(user):
            return None

        from app.models.teacher import Teacher
        result = await db.execute(
            select(Teacher.id).where(Teacher.user_id == user.id)
        )
        row = result.scalar_one_or_none()
        return row


# 便捷函数：创建权限检查依赖
def require_permission(resource: str, action: str):
    """创建权限检查依赖"""
    return Depends(PermissionChecker(resource, action))


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]

# 常用权限检查快捷方式
# Dashboard
DashboardRead = Annotated[User, Depends(PermissionChecker("dashboard", "read"))]

# Student
StudentRead = Annotated[User, Depends(PermissionChecker("student", "read"))]
StudentEdit = Annotated[User, Depends(PermissionChecker("student", "edit"))]
StudentDelete = Annotated[User, Depends(PermissionChecker("student", "delete"))]

# Teacher
TeacherRead = Annotated[User, Depends(PermissionChecker("teacher", "read"))]
TeacherEdit = Annotated[User, Depends(PermissionChecker("teacher", "edit"))]
TeacherDelete = Annotated[User, Depends(PermissionChecker("teacher", "delete"))]

# Course
CourseRead = Annotated[User, Depends(PermissionChecker("course", "read"))]
CourseEdit = Annotated[User, Depends(PermissionChecker("course", "edit"))]
CourseDelete = Annotated[User, Depends(PermissionChecker("course", "delete"))]

# ClassPlan
ClassPlanRead = Annotated[User, Depends(PermissionChecker("class_plan", "read"))]
ClassPlanEdit = Annotated[User, Depends(PermissionChecker("class_plan", "edit"))]
ClassPlanDelete = Annotated[User, Depends(PermissionChecker("class_plan", "delete"))]

# Enrollment
EnrollmentRead = Annotated[User, Depends(PermissionChecker("enrollment", "read"))]
EnrollmentEdit = Annotated[User, Depends(PermissionChecker("enrollment", "edit"))]
EnrollmentDelete = Annotated[User, Depends(PermissionChecker("enrollment", "delete"))]

# Schedule
ScheduleRead = Annotated[User, Depends(PermissionChecker("schedule", "read"))]
ScheduleEdit = Annotated[User, Depends(PermissionChecker("schedule", "edit"))]
ScheduleDelete = Annotated[User, Depends(PermissionChecker("schedule", "delete"))]

# Campus
CampusRead = Annotated[User, Depends(PermissionChecker("campus", "read"))]
CampusEdit = Annotated[User, Depends(PermissionChecker("campus", "edit"))]
CampusDelete = Annotated[User, Depends(PermissionChecker("campus", "delete"))]

# Classroom
ClassroomRead = Annotated[User, Depends(PermissionChecker("classroom", "read"))]
ClassroomEdit = Annotated[User, Depends(PermissionChecker("classroom", "edit"))]
ClassroomDelete = Annotated[User, Depends(PermissionChecker("classroom", "delete"))]

# User
UserRead = Annotated[User, Depends(PermissionChecker("user", "read"))]
UserEdit = Annotated[User, Depends(PermissionChecker("user", "edit"))]
UserDelete = Annotated[User, Depends(PermissionChecker("user", "delete"))]

# Dictionary
DictionaryRead = Annotated[User, Depends(PermissionChecker("dictionary", "read"))]
DictionaryEdit = Annotated[User, Depends(PermissionChecker("dictionary", "edit"))]
DictionaryDelete = Annotated[User, Depends(PermissionChecker("dictionary", "delete"))]

# RolePermission
RolePermissionRead = Annotated[User, Depends(PermissionChecker("role_permission", "read"))]
RolePermissionEdit = Annotated[User, Depends(PermissionChecker("role_permission", "edit"))]
RolePermissionDelete = Annotated[User, Depends(PermissionChecker("role_permission", "delete"))]

# System
SystemRead = Annotated[User, Depends(PermissionChecker("system", "read"))]
SystemEdit = Annotated[User, Depends(PermissionChecker("system", "edit"))]
SystemDelete = Annotated[User, Depends(PermissionChecker("system", "delete"))]
