"""
Permission service for RBAC management.
角色权限管理服务，处理角色、权限的增删改查。
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.permission import Resource, Permission, UserRole, RolePermission
from app.schemas.permission import (
    RoleCreate, RoleUpdate, ResourceWithPermissions, RoleWithPermissions
)
from app.api.deps import clear_permission_cache


class PermissionService:
    """权限管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Resource 相关 ====================

    async def get_all_resources(self) -> List[ResourceWithPermissions]:
        """获取所有资源及其权限"""
        result = await self.db.execute(
            select(Resource)
            .options(selectinload(Resource.permissions))
            .where(Resource.is_active == True)
            .order_by(Resource.sort_order)
        )
        resources = result.scalars().all()
        return [ResourceWithPermissions.model_validate(r) for r in resources]

    async def get_resource_by_code(self, code: str) -> Optional[Resource]:
        """根据编码获取资源"""
        result = await self.db.execute(
            select(Resource).where(Resource.code == code)
        )
        return result.scalar_one_or_none()

    # ==================== Role 相关 ====================

    async def get_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> Tuple[List[UserRole], int]:
        """获取角色列表（分页）"""
        query = select(UserRole)

        if is_active is not None:
            query = query.where(UserRole.is_active == is_active)

        # 总数
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # 分页数据
        query = query.order_by(UserRole.id).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        roles = result.scalars().all()

        return list(roles), total

    async def get_role_by_id(self, role_id: int) -> Optional[UserRole]:
        """根据ID获取角色"""
        result = await self.db.execute(
            select(UserRole).where(UserRole.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_role_by_code(self, code: str) -> Optional[UserRole]:
        """根据编码获取角色"""
        result = await self.db.execute(
            select(UserRole).where(UserRole.code == code)
        )
        return result.scalar_one_or_none()

    async def get_role_with_permissions(self, role_id: int) -> RoleWithPermissions:
        """获取角色及其权限详情"""
        result = await self.db.execute(
            select(UserRole)
            .options(selectinload(UserRole.role_permissions).selectinload(RolePermission.permission))
            .where(UserRole.id == role_id)
        )
        role = result.scalar_one_or_none()

        if not role:
            raise NotFoundException("角色不存在")

        # 构建返回数据
        permissions = [rp.permission for rp in role.role_permissions if rp.permission]

        return RoleWithPermissions(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_time=role.created_time,
            permissions=permissions
        )

    async def create_role(self, data: RoleCreate, created_by: str) -> UserRole:
        """创建角色"""
        # 检查编码是否重复
        existing = await self.get_role_by_code(data.code)
        if existing:
            raise BadRequestException(f"角色编码 {data.code} 已存在")

        role = UserRole(
            code=data.code,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            is_system=False,
            created_by=created_by
        )
        self.db.add(role)
        await self.db.flush()

        # 添加权限
        if data.permission_ids:
            await self._update_role_permissions(role.id, data.permission_ids)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update_role(self, role_id: int, data: RoleUpdate, updated_by: str) -> UserRole:
        """更新角色"""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("角色不存在")

        # 系统内置角色不能修改编码
        if role.is_system and hasattr(data, 'code') and data.code:
            raise BadRequestException("系统内置角色不能修改编码")

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)

        role.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(role)

        # 清除权限缓存
        clear_permission_cache()

        return role

    async def delete_role(self, role_id: int) -> None:
        """删除角色"""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("角色不存在")

        if role.is_system:
            raise BadRequestException("系统内置角色不能删除")

        # 检查是否有用户使用此角色
        from app.models.user import User
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.role_id == role_id)
        )
        user_count = result.scalar() or 0
        if user_count > 0:
            raise BadRequestException(f"有 {user_count} 个用户正在使用此角色，无法删除")

        await self.db.delete(role)
        await self.db.commit()

        # 清除权限缓存
        clear_permission_cache()

    async def update_role_permissions(self, role_id: int, permission_ids: List[int]) -> None:
        """更新角色权限"""
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("角色不存在")

        await self._update_role_permissions(role_id, permission_ids)
        await self.db.commit()

        # 清除权限缓存
        clear_permission_cache()

    async def _update_role_permissions(self, role_id: int, permission_ids: List[int]) -> None:
        """内部方法：更新角色权限关联"""
        # 删除现有权限关联
        await self.db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )

        # 添加新的权限关联
        for perm_id in permission_ids:
            rp = RolePermission(role_id=role_id, permission_id=perm_id)
            self.db.add(rp)

    # ==================== Permission 相关 ====================

    async def get_all_permissions(self) -> List[Permission]:
        """获取所有权限"""
        result = await self.db.execute(
            select(Permission)
            .join(Resource, Permission.resource_id == Resource.id)
            .where(Resource.is_active == True)
            .order_by(Resource.sort_order, Permission.action)
        )
        return list(result.scalars().all())

    async def get_permissions_by_role_id(self, role_id: int) -> List[str]:
        """获取角色的权限列表（格式：resource:action）"""
        result = await self.db.execute(
            select(Resource.code, Permission.action)
            .join(Permission, Permission.resource_id == Resource.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return [f"{row.code}:{row.action}" for row in result]


# ==================== 初始化数据 ====================

async def init_permission_data(db: AsyncSession) -> None:
    """
    初始化权限数据。
    创建资源、权限、角色及其关联。
    应在数据库迁移后调用一次。
    """
    # 检查是否已初始化
    result = await db.execute(select(func.count()).select_from(Resource))
    if result.scalar() > 0:
        return  # 已有数据，跳过

    # 资源模块定义
    resources_data = [
        {"code": "dashboard", "name": "仪表盘", "sort_order": 1},
        {"code": "student", "name": "学生管理", "sort_order": 2},
        {"code": "teacher", "name": "教师管理", "sort_order": 3},
        {"code": "course", "name": "课程管理", "sort_order": 4},
        {"code": "class_plan", "name": "开班计划", "sort_order": 5},
        {"code": "enrollment", "name": "报名管理", "sort_order": 6},
        {"code": "schedule", "name": "课表管理", "sort_order": 7},
        {"code": "campus", "name": "校区管理", "sort_order": 8},
        {"code": "classroom", "name": "教室管理", "sort_order": 9},
        {"code": "user", "name": "用户管理", "sort_order": 10},
        {"code": "dictionary", "name": "数据字典", "sort_order": 11},
        {"code": "role_permission", "name": "角色权限", "sort_order": 12},
        {"code": "system", "name": "系统设置", "sort_order": 13},
    ]

    # 操作类型
    actions = [
        {"action": "read", "name_suffix": "查看"},
        {"action": "edit", "name_suffix": "编辑"},
        {"action": "delete", "name_suffix": "删除"},
    ]

    # 创建资源和权限
    permission_map = {}  # resource_code:action -> permission_id
    for res_data in resources_data:
        resource = Resource(**res_data)
        db.add(resource)
        await db.flush()

        for act_data in actions:
            perm = Permission(
                resource_id=resource.id,
                action=act_data["action"],
                name=f"{res_data['name']}{act_data['name_suffix']}"
            )
            db.add(perm)
            await db.flush()
            permission_map[f"{res_data['code']}:{act_data['action']}"] = perm.id

    # 角色定义及权限配置
    roles_config = {
        "super_admin": {
            "name": "超级管理员",
            "description": "拥有所有权限",
            "is_system": True,
            "permissions": "all"  # 全部权限
        },
        "campus_admin": {
            "name": "校区管理员",
            "description": "管理本校区的学生、课程、排课等",
            "is_system": True,
            "permissions": [
                "dashboard:read",
                "student:read", "student:edit", "student:delete",
                "teacher:read",  # 教师只读
                "course:read", "course:edit", "course:delete",
                "class_plan:read", "class_plan:edit", "class_plan:delete",
                "enrollment:read", "enrollment:edit", "enrollment:delete",
                "schedule:read", "schedule:edit", "schedule:delete",
                "classroom:read",  # 教室只读
            ]
        },
        "teacher": {
            "name": "教师",
            "description": "查看课表、学生信息等",
            "is_system": True,
            "permissions": [
                "dashboard:read",
                "student:read",
                "class_plan:read",
                "enrollment:read",
                "schedule:read",
            ]
        },
        "student": {
            "name": "学生",
            "description": "查看自己的课表、报名信息",
            "is_system": True,
            "permissions": [
                "dashboard:read",
                "class_plan:read",
                "enrollment:read",
                "schedule:read",
            ]
        },
    }

    for role_code, config in roles_config.items():
        role = UserRole(
            code=role_code,
            name=config["name"],
            description=config["description"],
            is_system=config["is_system"],
            is_active=True
        )
        db.add(role)
        await db.flush()

        # 添加权限
        if config["permissions"] == "all":
            # 全部权限
            perm_ids = list(permission_map.values())
        else:
            # 指定权限
            perm_ids = [permission_map[p] for p in config["permissions"] if p in permission_map]

        for perm_id in perm_ids:
            rp = RolePermission(role_id=role.id, permission_id=perm_id)
            db.add(rp)

    await db.commit()
    print("权限数据初始化完成！")
