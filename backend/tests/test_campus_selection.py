"""
Campus selection unit tests.
校区选择功能单元测试：测试登录后校区选择流程和JWT中的campus_id。
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.campus import Campus
from app.models.teacher import Teacher
from app.models.class_plan import ClassPlan
from app.models.permission import UserRole
from app.core.security import create_access_token, verify_token


class TestLoginCampusSelection:
    """测试登录时的校区选择逻辑"""

    @pytest.mark.asyncio
    async def test_super_admin_login_returns_all_campuses(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """超级管理员登录应该返回所有校区供选择"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        assert response.status_code == 200
        data = response.json()

        # 超管有多个校区时需要选择
        assert "need_select_campus" in data["data"]
        assert "available_campuses" in data["data"]

        # 有两个测试校区时应该需要选择
        if len(test_campuses) > 1:
            assert data["data"]["need_select_campus"] is True
            assert len(data["data"]["available_campuses"]) == len(test_campuses)
        else:
            # 只有一个校区时自动选择
            assert data["data"]["need_select_campus"] is False

    @pytest.mark.asyncio
    async def test_campus_admin_login_auto_select_campus(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """校区管理员登录应该自动选择其所属校区"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "bj_admin", "password": "123456"}
        )
        assert response.status_code == 200
        data = response.json()

        # 校区管理员不需要选择校区
        assert data["data"]["need_select_campus"] is False
        # 应该自动设置为其所属校区
        assert data["data"]["current_campus_id"] == test_campuses[0].id

    @pytest.mark.asyncio
    async def test_student_login_auto_select_campus(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """学生登录应该自动选择其所属校区"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "student1", "password": "123456"}
        )
        assert response.status_code == 200
        data = response.json()

        # 学生不需要选择校区
        assert data["data"]["need_select_campus"] is False
        # 应该自动设置为其所属校区
        assert data["data"]["current_campus_id"] == test_campuses[0].id

    @pytest.mark.asyncio
    async def test_login_response_contains_tokens(
        self,
        client: AsyncClient,
        test_users: dict[str, User]
    ):
        """登录响应应该包含access_token和refresh_token"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"


class TestSelectCampusEndpoint:
    """测试校区选择接口"""

    @pytest.mark.asyncio
    async def test_super_admin_can_select_any_campus(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """超级管理员可以选择任意校区"""
        # 先登录获取token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        # 选择北京校区
        response = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token}"},
            json={"campus_id": test_campuses[0].id}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["data"]["need_select_campus"] is False
        assert data["data"]["current_campus_id"] == test_campuses[0].id

        # 新token应该包含campus_id
        new_token = data["data"]["access_token"]
        payload = verify_token(new_token)
        assert payload["campus_id"] == test_campuses[0].id

    @pytest.mark.asyncio
    async def test_super_admin_can_switch_campus(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """超级管理员可以切换校区"""
        # 登录获取token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        # 选择北京校区
        response1 = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token}"},
            json={"campus_id": test_campuses[0].id}
        )
        token1 = response1.json()["data"]["access_token"]

        # 切换到上海校区
        response2 = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token1}"},
            json={"campus_id": test_campuses[1].id}
        )
        assert response2.status_code == 200

        # 验证新token中的campus_id
        new_token = response2.json()["data"]["access_token"]
        payload = verify_token(new_token)
        assert payload["campus_id"] == test_campuses[1].id

    @pytest.mark.asyncio
    async def test_campus_admin_cannot_select_other_campus(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """校区管理员不能选择其他校区"""
        # 登录获取token（北京校区管理员）
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "bj_admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        # 尝试选择上海校区（应该被拒绝）
        response = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token}"},
            json={"campus_id": test_campuses[1].id}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_select_invalid_campus_returns_error(
        self,
        client: AsyncClient,
        test_users: dict[str, User]
    ):
        """选择不存在的校区应该返回错误"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token}"},
            json={"campus_id": 99999}
        )
        assert response.status_code == 400


class TestJWTCampusId:
    """测试JWT中的campus_id"""

    @pytest.mark.asyncio
    async def test_token_contains_campus_id(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """Token应该包含选中的campus_id"""
        # 校区管理员登录，自动设置campus_id
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "bj_admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        # 验证token payload
        payload = verify_token(token)
        assert payload is not None
        assert payload["campus_id"] == test_campuses[0].id

    @pytest.mark.asyncio
    async def test_token_contains_role_code(
        self,
        client: AsyncClient,
        test_users: dict[str, User]
    ):
        """Token应该包含role_code"""
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "bj_admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        payload = verify_token(token)
        assert payload is not None
        assert payload["role_code"] == "campus_admin"

    @pytest.mark.asyncio
    async def test_refresh_token_preserves_campus_id(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus]
    ):
        """刷新token应该保留campus_id"""
        # 登录获取token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        access_token = login_response.json()["data"]["access_token"]
        refresh_token = login_response.json()["data"]["refresh_token"]

        # 选择校区
        select_response = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"campus_id": test_campuses[0].id}
        )
        new_refresh_token = select_response.json()["data"]["refresh_token"]

        # 刷新token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh_token}
        )
        assert refresh_response.status_code == 200

        # 验证新token仍包含campus_id
        refreshed_token = refresh_response.json()["data"]["access_token"]
        payload = verify_token(refreshed_token)
        assert payload["campus_id"] == test_campuses[0].id


class TestTeacherCampusSelection:
    """测试教师的校区选择逻辑"""

    @pytest_asyncio.fixture
    async def teacher_with_classes(
        self,
        db_session: AsyncSession,
        test_users: dict[str, User],
        test_campuses: list[Campus],
        test_class_plans: list[ClassPlan],
        test_teachers: list[Teacher]
    ):
        """
        创建一个在多个校区有课的教师用户。
        注意：测试教师(test_teachers[0])在北京校区的班级中教课。
        """
        # test_teachers[0] 已经关联到北京校区的班级
        # 需要再创建一个上海校区的班级，让这个教师也教
        from app.models.class_plan import ClassPlan as CP
        from app.models.course import Course

        # 获取上海校区的课程
        sh_course = test_class_plans[1].course_id

        # 创建上海校区的班级，由同一个教师教
        new_class = CP(
            name="跨校区数学班",
            course_id=sh_course,
            campus_id=test_campuses[1].id,
            teacher_id=test_teachers[0].id,  # 同一个教师
            max_students=15,
            status="ongoing",
            is_active=True,
            created_by="test",
        )
        db_session.add(new_class)
        await db_session.flush()

        # 创建一个关联到该教师的用户
        from app.models.permission import UserRole
        from sqlalchemy import select

        result = await db_session.execute(
            select(UserRole).where(UserRole.code == "teacher")
        )
        teacher_role = result.scalar_one()

        teacher_user = User(
            username="multi_campus_teacher",
            phone="13800000099",
            hashed_password=test_users["teacher"].hashed_password,
            role="teacher",
            role_id=teacher_role.id,
            is_active=True,
            created_by="test",
        )
        db_session.add(teacher_user)
        await db_session.flush()

        # 关联教师记录到用户
        test_teachers[0].user_id = teacher_user.id
        await db_session.flush()

        return teacher_user

    @pytest.mark.asyncio
    async def test_teacher_with_multiple_campuses_needs_selection(
        self,
        client: AsyncClient,
        teacher_with_classes: User,
        test_campuses: list[Campus]
    ):
        """在多个校区有课的教师登录应该需要选择校区"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "multi_campus_teacher", "password": "123456"}
        )
        assert response.status_code == 200
        data = response.json()

        # 应该需要选择校区
        assert data["data"]["need_select_campus"] is True
        # 应该有2个校区可选
        assert len(data["data"]["available_campuses"]) == 2

    @pytest.mark.asyncio
    async def test_teacher_can_only_select_available_campus(
        self,
        client: AsyncClient,
        teacher_with_classes: User,
        test_campuses: list[Campus]
    ):
        """教师只能选择有课的校区"""
        # 登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "multi_campus_teacher", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]
        available = login_response.json()["data"]["available_campuses"]

        # 选择可用的校区应该成功
        available_campus_id = available[0]["id"]
        response = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token}"},
            json={"campus_id": available_campus_id}
        )
        assert response.status_code == 200


class TestCampusScopedDataFiltering:
    """测试基于JWT campus_id的数据过滤"""

    @pytest.mark.asyncio
    async def test_data_filtered_by_selected_campus(
        self,
        client: AsyncClient,
        test_users: dict[str, User],
        test_campuses: list[Campus],
        test_students: list
    ):
        """数据应该根据选中的校区过滤"""
        # 超管登录并选择北京校区
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        token = login_response.json()["data"]["access_token"]

        select_response = await client.post(
            "/api/v1/auth/select-campus",
            headers={"Authorization": f"Bearer {token}"},
            json={"campus_id": test_campuses[0].id}
        )
        campus_token = select_response.json()["data"]["access_token"]

        # 获取学生列表
        students_response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {campus_token}"}
        )

        # 应该成功获取数据
        assert students_response.status_code == 200
        # 数据应该被过滤为北京校区的学生
        data = students_response.json()
        if "items" in data["data"]:
            for student in data["data"]["items"]:
                # 学生应该属于选中的校区
                if "campus_id" in student:
                    assert student["campus_id"] == test_campuses[0].id
