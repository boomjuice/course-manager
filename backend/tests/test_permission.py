"""
Permission module unit tests.
权限模块单元测试：资源、权限、角色、角色权限关联的CRUD测试。
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Resource, Permission, UserRole, RolePermission
from app.services.permission_service import PermissionService


class TestPermissionService:
    """测试Permission服务层"""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> PermissionService:
        """创建服务实例"""
        return PermissionService(db_session)

    # ==================== Resource 相关测试 ====================

    @pytest.mark.asyncio
    async def test_get_all_resources(
        self, service: PermissionService, test_resources: list[Resource]
    ):
        """测试获取所有资源"""
        resources = await service.get_all_resources()
        assert len(resources) == len(test_resources)
        # 检查排序是否正确
        codes = [r.code for r in resources]
        assert "dashboard" in codes
        assert "student" in codes

    @pytest.mark.asyncio
    async def test_get_resource_by_code(
        self, service: PermissionService, test_resources: list[Resource]
    ):
        """测试根据编码获取资源"""
        resource = await service.get_resource_by_code("student")
        assert resource is not None
        assert resource.name == "学生管理"

    @pytest.mark.asyncio
    async def test_get_resource_by_code_not_found(self, service: PermissionService):
        """测试获取不存在的资源"""
        resource = await service.get_resource_by_code("nonexistent")
        assert resource is None

    # ==================== Role 相关测试 ====================

    @pytest.mark.asyncio
    async def test_get_roles(
        self, service: PermissionService, test_roles: dict[str, UserRole]
    ):
        """测试获取角色列表"""
        roles, total = await service.get_roles(page=1, page_size=20)
        assert total == len(test_roles)
        assert len(roles) == total

    @pytest.mark.asyncio
    async def test_get_roles_with_active_filter(
        self, service: PermissionService, test_roles: dict[str, UserRole]
    ):
        """测试获取活跃角色"""
        roles, total = await service.get_roles(page=1, page_size=20, is_active=True)
        assert total == len(test_roles)  # 所有测试角色都是活跃的

    @pytest.mark.asyncio
    async def test_get_role_by_id(
        self, service: PermissionService, test_roles: dict[str, UserRole]
    ):
        """测试根据ID获取角色"""
        super_admin = test_roles["super_admin"]
        role = await service.get_role_by_id(super_admin.id)
        assert role is not None
        assert role.code == "super_admin"
        assert role.name == "超级管理员"

    @pytest.mark.asyncio
    async def test_get_role_by_code(
        self, service: PermissionService, test_roles: dict[str, UserRole]
    ):
        """测试根据编码获取角色"""
        role = await service.get_role_by_code("campus_admin")
        assert role is not None
        assert role.name == "校区管理员"

    @pytest.mark.asyncio
    async def test_get_role_with_permissions(
        self,
        service: PermissionService,
        test_roles: dict[str, UserRole],
        test_permissions: list[Permission]
    ):
        """测试获取角色及权限详情"""
        super_admin = test_roles["super_admin"]
        role_detail = await service.get_role_with_permissions(super_admin.id)
        assert role_detail is not None
        assert role_detail.code == "super_admin"
        # 超级管理员应该有所有权限
        assert len(role_detail.permissions) == len(test_permissions)

    @pytest.mark.asyncio
    async def test_create_role(
        self,
        service: PermissionService,
        db_session: AsyncSession,
        test_permissions: list[Permission]
    ):
        """测试创建角色"""
        from app.schemas.permission import RoleCreate

        perm_ids = [p.id for p in test_permissions[:3]]  # 取前3个权限
        data = RoleCreate(
            code="test_role",
            name="测试角色",
            description="这是一个测试角色",
            is_active=True,
            permission_ids=perm_ids
        )
        role = await service.create_role(data, created_by="test_user")

        assert role is not None
        assert role.code == "test_role"
        assert role.name == "测试角色"
        assert role.is_system is False  # 用户创建的角色不是系统角色

    @pytest.mark.asyncio
    async def test_create_role_duplicate_code(
        self,
        service: PermissionService,
        test_roles: dict[str, UserRole]
    ):
        """测试创建重复编码的角色应该失败"""
        from app.schemas.permission import RoleCreate
        from app.core.exceptions import BadRequestException

        data = RoleCreate(
            code="super_admin",  # 已存在的编码
            name="重复角色",
            is_active=True
        )

        with pytest.raises(BadRequestException) as exc_info:
            await service.create_role(data, created_by="test_user")
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role(
        self,
        service: PermissionService,
        db_session: AsyncSession,
        test_permissions: list[Permission]
    ):
        """测试更新角色"""
        from app.schemas.permission import RoleCreate, RoleUpdate

        # 先创建一个测试角色
        create_data = RoleCreate(
            code="updatable_role",
            name="待更新角色",
            is_active=True
        )
        role = await service.create_role(create_data, created_by="test_user")

        # 更新角色
        update_data = RoleUpdate(name="已更新角色", description="更新后的描述")
        updated_role = await service.update_role(role.id, update_data, updated_by="test_user")

        assert updated_role.name == "已更新角色"
        assert updated_role.description == "更新后的描述"

    @pytest.mark.asyncio
    async def test_delete_role(
        self,
        service: PermissionService,
        db_session: AsyncSession
    ):
        """测试删除角色"""
        from app.schemas.permission import RoleCreate

        # 先创建一个测试角色
        data = RoleCreate(
            code="deletable_role",
            name="待删除角色",
            is_active=True
        )
        role = await service.create_role(data, created_by="test_user")
        role_id = role.id

        # 删除角色
        await service.delete_role(role_id)

        # 验证已删除
        deleted_role = await service.get_role_by_id(role_id)
        assert deleted_role is None

    @pytest.mark.asyncio
    async def test_delete_system_role_should_fail(
        self,
        service: PermissionService,
        test_roles: dict[str, UserRole]
    ):
        """测试删除系统内置角色应该失败"""
        from app.core.exceptions import BadRequestException

        super_admin = test_roles["super_admin"]

        with pytest.raises(BadRequestException) as exc_info:
            await service.delete_role(super_admin.id)
        assert "系统内置角色不能删除" in str(exc_info.value)

    # ==================== RolePermission 相关测试 ====================

    @pytest.mark.asyncio
    async def test_update_role_permissions(
        self,
        service: PermissionService,
        db_session: AsyncSession,
        test_permissions: list[Permission]
    ):
        """测试更新角色权限"""
        from app.schemas.permission import RoleCreate

        # 创建角色，初始没有权限
        data = RoleCreate(
            code="perm_test_role",
            name="权限测试角色",
            is_active=True
        )
        role = await service.create_role(data, created_by="test_user")

        # 添加权限
        new_perm_ids = [p.id for p in test_permissions[:5]]
        await service.update_role_permissions(role.id, new_perm_ids)

        # 验证权限已更新
        role_detail = await service.get_role_with_permissions(role.id)
        assert len(role_detail.permissions) == 5

    @pytest.mark.asyncio
    async def test_get_all_permissions(
        self,
        service: PermissionService,
        test_permissions: list[Permission]
    ):
        """测试获取所有权限"""
        permissions = await service.get_all_permissions()
        assert len(permissions) == len(test_permissions)

    @pytest.mark.asyncio
    async def test_get_permissions_by_role_id(
        self,
        service: PermissionService,
        test_roles: dict[str, UserRole],
        test_permissions: list[Permission]
    ):
        """测试获取角色的权限列表"""
        super_admin = test_roles["super_admin"]
        permissions = await service.get_permissions_by_role_id(super_admin.id)

        # 超级管理员应该有所有权限
        assert len(permissions) == len(test_permissions)

        # 检查格式是否正确 (resource:action)
        for perm in permissions:
            assert ":" in perm
            parts = perm.split(":")
            assert len(parts) == 2
            assert parts[1] in ["read", "edit", "delete"]


class TestPermissionAPI:
    """测试Permission API端点"""

    @pytest.mark.asyncio
    async def test_get_resources_as_super_admin(
        self,
        client: AsyncClient,
        test_resources: list[Resource],
        test_users,
        super_admin_token: str
    ):
        """超级管理员获取资源列表"""
        response = await client.get(
            "/api/v1/permissions/resources",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == len(test_resources)

    @pytest.mark.asyncio
    async def test_get_resources_as_campus_admin(
        self,
        client: AsyncClient,
        test_resources: list[Resource],
        test_users,
        bj_admin_token: str
    ):
        """校区管理员获取资源列表应该被禁止"""
        response = await client.get(
            "/api/v1/permissions/resources",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        # 校区管理员没有role_permission:read权限
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_roles_as_super_admin(
        self,
        client: AsyncClient,
        test_roles: dict[str, UserRole],
        test_users,
        super_admin_token: str
    ):
        """超级管理员获取角色列表"""
        response = await client.get(
            "/api/v1/permissions/roles",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == len(test_roles)

    @pytest.mark.asyncio
    async def test_get_role_detail(
        self,
        client: AsyncClient,
        test_roles: dict[str, UserRole],
        test_users,
        super_admin_token: str
    ):
        """获取角色详情"""
        super_admin = test_roles["super_admin"]
        response = await client.get(
            f"/api/v1/permissions/roles/{super_admin.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["code"] == "super_admin"
        assert "permissions" in data["data"]

    @pytest.mark.asyncio
    async def test_create_role(
        self,
        client: AsyncClient,
        test_users,
        test_permissions: list[Permission],
        super_admin_token: str
    ):
        """创建角色"""
        perm_ids = [p.id for p in test_permissions[:3]]
        response = await client.post(
            "/api/v1/permissions/roles",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "code": "api_test_role",
                "name": "API测试角色",
                "description": "通过API创建的测试角色",
                "is_active": True,
                "permission_ids": perm_ids
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["code"] == "api_test_role"

    @pytest.mark.asyncio
    async def test_update_role_permissions(
        self,
        client: AsyncClient,
        test_users,
        test_roles: dict[str, UserRole],
        test_permissions: list[Permission],
        super_admin_token: str
    ):
        """更新角色权限"""
        # 使用campus_admin角色测试
        campus_admin = test_roles["campus_admin"]
        new_perm_ids = [p.id for p in test_permissions[:5]]

        response = await client.put(
            f"/api/v1/permissions/roles/{campus_admin.id}/permissions",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={"permission_ids": new_perm_ids}  # 需要用RolePermissionUpdate格式
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_custom_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_users,
        test_permissions: list[Permission],
        super_admin_token: str
    ):
        """删除自定义角色"""
        # 先创建一个角色
        response = await client.post(
            "/api/v1/permissions/roles",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "code": "to_delete_role",
                "name": "待删除角色",
                "is_active": True
            }
        )
        assert response.status_code == 200
        role_id = response.json()["data"]["id"]

        # 删除角色
        response = await client.delete(
            f"/api/v1/permissions/roles/{role_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_system_role_should_fail(
        self,
        client: AsyncClient,
        test_users,
        test_roles: dict[str, UserRole],
        super_admin_token: str
    ):
        """删除系统内置角色应该失败"""
        super_admin = test_roles["super_admin"]
        response = await client.delete(
            f"/api/v1/permissions/roles/{super_admin.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_current_user_permissions(
        self,
        client: AsyncClient,
        test_users,
        super_admin_token: str
    ):
        """获取当前用户权限"""
        response = await client.get(
            "/api/v1/permissions/current",  # 正确的路由路径
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "role_code" in data["data"]
        assert "permissions" in data["data"]
        assert data["data"]["role_code"] == "super_admin"
