"""
RBAC permission check unit tests.
RBAC权限检查单元测试：测试PermissionChecker和CampusScopedQuery。
"""
import pytest
import pytest_asyncio
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    PermissionChecker, CampusScopedQuery, get_user_permissions,
    clear_permission_cache
)
from app.models.user import User
from app.models.permission import UserRole


class TestPermissionChecker:
    """测试RBAC权限检查器"""

    @pytest.mark.asyncio
    async def test_super_admin_has_all_permissions(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        super_admin_token: str
    ):
        """超级管理员应该拥有所有权限"""
        # 测试各种资源的访问
        endpoints = [
            "/api/v1/students",
            "/api/v1/courses",
            "/api/v1/teachers",
            "/api/v1/schedules",
            "/api/v1/enrollments",
            "/api/v1/permissions/roles",
        ]
        for endpoint in endpoints:
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {super_admin_token}"}
            )
            # 200或404都可以，关键不是403（无权限）
            assert response.status_code != 403, f"超级管理员访问{endpoint}被拒绝"

    @pytest.mark.asyncio
    async def test_campus_admin_student_read(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """校区管理员应该有student:read权限"""
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        # 有权限，返回200或者其他业务相关状态码，但不应该是403
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_campus_admin_no_role_permission(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """校区管理员不应该有role_permission:read权限"""
        response = await client.get(
            "/api/v1/permissions/roles",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_read_only_permissions(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        teacher_token: str
    ):
        """教师应该只有只读权限"""
        # 读取操作应该成功
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        # 教师有student:read权限
        assert response.status_code != 403

        # 创建操作应该被拒绝
        response = await client.post(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "name": "测试学生",
                "phone": "13800138000",
                "campus_id": 1
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_student_limited_permissions(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        student_token: str
    ):
        """学生应该有非常有限的权限"""
        # 学生没有student:read权限（只能看自己）
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403

        # 学生有schedule:read权限
        response = await client.get(
            "/api/v1/schedules",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_unauthorized_no_token(self, client: AsyncClient):
        """无Token应该返回401"""
        response = await client.get("/api/v1/students")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthorized_invalid_token(self, client: AsyncClient):
        """无效Token应该返回401"""
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401


class TestCampusScopedQuery:
    """
    测试校区数据范围过滤。
    注意：新架构下campus_id从JWT token中读取（_token_campus_id属性），
    而不是从数据库user.campus_id字段读取。
    """

    def test_super_admin_no_filter(self, test_users: dict[str, User]):
        """超级管理员未选择校区时应该无校区过滤"""
        scope = CampusScopedQuery()
        super_admin = test_users["super_admin"]
        # 模拟未选择校区（JWT中没有campus_id）
        super_admin._token_campus_id = None
        super_admin._token_role_code = "super_admin"
        campus_id = scope.get_campus_filter(super_admin)
        assert campus_id is None

    def test_super_admin_with_selected_campus(self, test_users: dict[str, User]):
        """超级管理员选择校区后应该有校区过滤"""
        scope = CampusScopedQuery()
        super_admin = test_users["super_admin"]
        # 模拟已选择校区
        super_admin._token_campus_id = 1
        super_admin._token_role_code = "super_admin"
        campus_id = scope.get_campus_filter(super_admin)
        assert campus_id == 1

    def test_campus_admin_has_filter(self, test_users: dict[str, User]):
        """校区管理员应该有校区过滤（从JWT获取）"""
        scope = CampusScopedQuery()
        bj_admin = test_users["bj_campus_admin"]
        # 模拟登录后JWT中包含的campus_id
        bj_admin._token_campus_id = bj_admin.campus_id
        bj_admin._token_role_code = "campus_admin"
        campus_id = scope.get_campus_filter(bj_admin)
        assert campus_id is not None
        assert campus_id == bj_admin.campus_id

    def test_teacher_has_filter(self, test_users: dict[str, User]):
        """教师应该有校区过滤（从JWT获取）"""
        scope = CampusScopedQuery()
        teacher = test_users["teacher"]
        # 模拟登录后JWT中包含的campus_id
        teacher._token_campus_id = teacher.campus_id
        teacher._token_role_code = "teacher"
        campus_id = scope.get_campus_filter(teacher)
        assert campus_id is not None
        assert campus_id == teacher.campus_id

    def test_student_has_filter(self, test_users: dict[str, User]):
        """学生应该有校区过滤（从JWT获取）"""
        scope = CampusScopedQuery()
        student = test_users["student"]
        # 模拟登录后JWT中包含的campus_id
        student._token_campus_id = student.campus_id
        student._token_role_code = "student"
        campus_id = scope.get_campus_filter(student)
        assert campus_id is not None
        assert campus_id == student.campus_id

    def test_is_super_admin(self, test_users: dict[str, User]):
        """测试is_super_admin方法"""
        scope = CampusScopedQuery()
        # 设置_token_role_code以便is_super_admin检查
        test_users["super_admin"]._token_role_code = "super_admin"
        test_users["bj_campus_admin"]._token_role_code = "campus_admin"
        test_users["teacher"]._token_role_code = "teacher"
        test_users["student"]._token_role_code = "student"

        assert scope.is_super_admin(test_users["super_admin"]) is True
        assert scope.is_super_admin(test_users["bj_campus_admin"]) is False
        assert scope.is_super_admin(test_users["teacher"]) is False
        assert scope.is_super_admin(test_users["student"]) is False


class TestPermissionCache:
    """测试权限缓存"""

    @pytest.mark.asyncio
    async def test_permission_cache_works(
        self,
        db_session: AsyncSession,
        test_users: dict[str, User],
        test_permissions
    ):
        """测试权限缓存机制"""
        clear_permission_cache()  # 清除缓存

        bj_admin = test_users["bj_campus_admin"]

        # 第一次获取，应该查询数据库
        perms1 = await get_user_permissions(db_session, bj_admin.id, bj_admin.role_id)
        assert len(perms1) > 0

        # 第二次获取，应该从缓存获取（相同结果）
        perms2 = await get_user_permissions(db_session, bj_admin.id, bj_admin.role_id)
        assert perms1 == perms2

    @pytest.mark.asyncio
    async def test_clear_permission_cache_by_user(
        self,
        db_session: AsyncSession,
        test_users: dict[str, User],
        test_permissions
    ):
        """测试按用户清除缓存"""
        bj_admin = test_users["bj_campus_admin"]
        sh_admin = test_users["sh_campus_admin"]

        # 先加载两个用户的权限到缓存
        await get_user_permissions(db_session, bj_admin.id, bj_admin.role_id)
        await get_user_permissions(db_session, sh_admin.id, sh_admin.role_id)

        # 清除bj_admin的缓存
        clear_permission_cache(user_id=bj_admin.id)

        # 再次获取时会重新查询（这里主要验证不报错）
        perms = await get_user_permissions(db_session, bj_admin.id, bj_admin.role_id)
        assert len(perms) > 0

    @pytest.mark.asyncio
    async def test_clear_all_permission_cache(
        self,
        db_session: AsyncSession,
        test_users: dict[str, User],
        test_permissions
    ):
        """测试清除所有缓存"""
        bj_admin = test_users["bj_campus_admin"]

        # 先加载权限到缓存
        await get_user_permissions(db_session, bj_admin.id, bj_admin.role_id)

        # 清除所有缓存
        clear_permission_cache()

        # 再次获取时会重新查询
        perms = await get_user_permissions(db_session, bj_admin.id, bj_admin.role_id)
        assert len(perms) > 0


class TestCrossRolePermissions:
    """测试跨角色权限边界"""

    @pytest.mark.asyncio
    async def test_bj_admin_cannot_access_sh_student(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_students,
        bj_admin_token: str
    ):
        """北京管理员不能访问上海校区的学生"""
        sh_student = test_students[1]  # 上海的学生

        response = await client.get(
            f"/api/v1/students/{sh_student.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        # 应该返回403或404（因为跨校区数据不可见）
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_sh_admin_cannot_access_bj_course(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_courses,
        sh_admin_token: str
    ):
        """上海管理员不能访问北京校区的课程"""
        bj_course = test_courses[0]  # 北京的课程

        response = await client.get(
            f"/api/v1/courses/{bj_course.id}",
            headers={"Authorization": f"Bearer {sh_admin_token}"}
        )
        # 应该返回403或404（因为跨校区数据不可见）
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_super_admin_can_access_selected_campus_data(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_students,
        test_courses,
        super_admin_token: str
    ):
        """
        超级管理员选择校区后只能访问该校区的数据。
        新架构下，超管token默认选择北京校区。
        """
        # 访问北京学生（应该成功，因为选择了北京校区）
        bj_student = test_students[0]
        response = await client.get(
            f"/api/v1/students/{bj_student.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200

        # 访问上海学生（应该失败，因为选择了北京校区）
        sh_student = test_students[1]
        response = await client.get(
            f"/api/v1/students/{sh_student.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        # 跨校区访问返回403或404
        assert response.status_code in [403, 404]

        # 访问北京课程（应该成功）
        bj_course = test_courses[0]
        response = await client.get(
            f"/api/v1/courses/{bj_course.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200

        # 访问上海课程（应该失败）
        sh_course = test_courses[1]
        response = await client.get(
            f"/api/v1/courses/{sh_course.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        # 跨校区访问返回403或404
        assert response.status_code in [403, 404]


class TestPermissionEdgeCases:
    """测试权限边界情况"""

    @pytest.mark.asyncio
    async def test_disabled_user_cannot_access(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """被禁用的用户不能访问系统"""
        # 禁用用户
        bj_admin = test_users["bj_campus_admin"]
        bj_admin.is_active = False
        await db_session.flush()

        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 401

        # 恢复用户状态
        bj_admin.is_active = True
        await db_session.flush()

    @pytest.mark.asyncio
    async def test_edit_permission_includes_create(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses,
        bj_admin_token: str
    ):
        """edit权限应该包含create功能"""
        # 校区管理员有student:edit权限，应该能创建学生
        response = await client.post(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "name": "权限测试学生",
                "phone": "13800138099",
                "campus_id": test_campuses[0].id,  # 北京校区
                "status": "active"
            }
        )
        # 应该成功或者其他业务错误，但不应该是403
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_delete_permission_required(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_students,
        teacher_token: str
    ):
        """没有delete权限不能删除"""
        # 教师没有student:delete权限
        student = test_students[0]
        response = await client.delete(
            f"/api/v1/students/{student.id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403
