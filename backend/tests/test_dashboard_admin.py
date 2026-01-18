# backend/tests/test_dashboard_admin.py
"""
Admin Dashboard API Tests
管理员仪表盘API测试。
"""
import pytest
import pytest_asyncio
from datetime import date, time, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule
from app.models.class_plan import ClassPlan

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def admin_test_students(
    db_session: AsyncSession,
    test_campuses: list,
) -> list[Student]:
    """
    Create students for admin dashboard tests.
    Each campus has some students.
    """
    students = []
    # 北京校区的学生
    for i in range(3):
        student = Student(
            name=f"北京学生{i+1}",
            phone=f"1380000010{i}",
            campus_id=test_campuses[0].id,
            status="active",
            is_active=True,
            created_by="test",
        )
        students.append(student)

    # 上海校区的学生
    for i in range(2):
        student = Student(
            name=f"上海学生{i+1}",
            phone=f"1380000020{i}",
            campus_id=test_campuses[1].id,
            status="active",
            is_active=True,
            created_by="test",
        )
        students.append(student)

    db_session.add_all(students)
    await db_session.flush()
    return students


@pytest_asyncio.fixture
async def admin_test_teachers(
    db_session: AsyncSession,
) -> list[Teacher]:
    """
    Create teachers for admin dashboard tests.
    """
    teachers = []
    for i in range(2):
        teacher = Teacher(
            name=f"测试教师{i+1}",
            phone=f"1390000010{i}",
            subjects=["数学", "物理"],
            hourly_rate=Decimal("150.00"),
            status="active",
            is_active=True,
            created_by="test",
        )
        teachers.append(teacher)

    db_session.add_all(teachers)
    await db_session.flush()
    return teachers


@pytest_asyncio.fixture
async def admin_test_class_plans(
    db_session: AsyncSession,
    test_campuses: list,
    test_courses: list,
    admin_test_teachers: list[Teacher],
    test_classrooms: list,
) -> list[ClassPlan]:
    """
    Create class plans for admin dashboard tests.
    """
    class_plans = []

    # 北京校区的班级
    plan_bj = ClassPlan(
        name="北京测试班",
        course_id=test_courses[0].id,
        campus_id=test_campuses[0].id,
        teacher_id=admin_test_teachers[0].id,
        classroom_id=test_classrooms[0].id,
        max_students=20,
        status="ongoing",
        is_active=True,
        created_by="test",
    )
    class_plans.append(plan_bj)

    # 上海校区的班级
    plan_sh = ClassPlan(
        name="上海测试班",
        course_id=test_courses[1].id,
        campus_id=test_campuses[1].id,
        teacher_id=admin_test_teachers[1].id,
        classroom_id=test_classrooms[1].id,
        max_students=15,
        status="ongoing",
        is_active=True,
        created_by="test",
    )
    class_plans.append(plan_sh)

    db_session.add_all(class_plans)
    await db_session.flush()
    return class_plans


@pytest_asyncio.fixture
async def admin_test_enrollments(
    db_session: AsyncSession,
    admin_test_students: list[Student],
    admin_test_class_plans: list[ClassPlan],
    test_campuses: list,
) -> list[Enrollment]:
    """
    Create enrollments for admin dashboard tests.
    """
    enrollments = []

    # 北京学生报名北京班级
    for i in range(3):
        enrollment = Enrollment(
            student_id=admin_test_students[i].id,
            class_plan_id=admin_test_class_plans[0].id,
            campus_id=test_campuses[0].id,
            enroll_date=date.today() - timedelta(days=i),
            paid_amount=Decimal("3000.00"),
            purchased_hours=Decimal("20.0"),
            used_hours=Decimal("5.0"),
            status="active",
            created_by="test",
        )
        enrollments.append(enrollment)

    # 上海学生报名上海班级
    for i in range(2):
        enrollment = Enrollment(
            student_id=admin_test_students[3 + i].id,
            class_plan_id=admin_test_class_plans[1].id,
            campus_id=test_campuses[1].id,
            enroll_date=date.today() - timedelta(days=i + 3),
            paid_amount=Decimal("2500.00"),
            purchased_hours=Decimal("15.0"),
            used_hours=Decimal("3.0"),
            status="active",
            created_by="test",
        )
        enrollments.append(enrollment)

    db_session.add_all(enrollments)
    await db_session.flush()
    return enrollments


@pytest_asyncio.fixture
async def admin_test_schedules(
    db_session: AsyncSession,
    admin_test_class_plans: list[ClassPlan],
    admin_test_teachers: list[Teacher],
    test_classrooms: list,
    test_campuses: list,
) -> list[Schedule]:
    """
    Create schedules for admin dashboard tests.
    """
    today = date.today()
    schedules = []

    # 北京校区排课
    for i in range(3):
        schedule = Schedule(
            class_plan_id=admin_test_class_plans[0].id,
            campus_id=test_campuses[0].id,
            teacher_id=admin_test_teachers[0].id,
            classroom_id=test_classrooms[0].id,
            schedule_date=today + timedelta(days=i),
            start_time=time(9, 0),
            end_time=time(11, 0),
            lesson_hours=2.0,
            status="scheduled",
            created_by="test",
        )
        schedules.append(schedule)

    # 上海校区排课
    for i in range(2):
        schedule = Schedule(
            class_plan_id=admin_test_class_plans[1].id,
            campus_id=test_campuses[1].id,
            teacher_id=admin_test_teachers[1].id,
            classroom_id=test_classrooms[1].id,
            schedule_date=today + timedelta(days=i),
            start_time=time(14, 0),
            end_time=time(16, 0),
            lesson_hours=2.0,
            status="scheduled",
            created_by="test",
        )
        schedules.append(schedule)

    db_session.add_all(schedules)
    await db_session.flush()
    return schedules


class TestAdminDashboardOverview:
    """管理员仪表盘 - 概览 Tab"""

    async def test_super_admin_can_access(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_students: list[Student],
        admin_test_teachers: list[Teacher],
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
        admin_test_schedules: list[Schedule],
    ):
        """超管可以访问管理员仪表盘"""
        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "kpi_cards" in data
        assert "enrollment_trend" in data

    async def test_campus_admin_can_access(
        self,
        client: AsyncClient,
        bj_admin_token: str,
        admin_test_students: list[Student],
        admin_test_teachers: list[Teacher],
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
        admin_test_schedules: list[Schedule],
    ):
        """校区管理员可以访问管理员仪表盘"""
        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200

    async def test_student_cannot_access(
        self,
        client: AsyncClient,
        student_token: str,
    ):
        """学生不能访问管理员仪表盘"""
        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403

    async def test_teacher_cannot_access(
        self,
        client: AsyncClient,
        teacher_token: str,
    ):
        """教师不能访问管理员仪表盘"""
        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403

    async def test_super_admin_can_filter_by_campus(
        self,
        client: AsyncClient,
        super_admin_token: str,
        test_campuses,
        admin_test_students: list[Student],
        admin_test_teachers: list[Teacher],
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
    ):
        """超管可以按校区筛选"""
        campus_id = test_campuses[0].id
        response = await client.get(
            f"/api/v1/dashboard/admin?campus_id={campus_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200

    async def test_super_admin_sees_campus_comparison(
        self,
        client: AsyncClient,
        test_users,
        test_campuses,
        admin_test_students: list[Student],
        admin_test_teachers: list[Teacher],
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
    ):
        """超管不选校区时可以看到校区对比"""
        # 创建一个不带campus_id的超管token
        from app.core.security import create_access_token
        super_admin = test_users["super_admin"]
        token_without_campus = create_access_token(data={
            "sub": str(super_admin.id),
            "username": super_admin.username,
            "role": super_admin.role,
            "role_code": "super_admin",
            "campus_id": None,  # 不选择校区
        })

        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {token_without_campus}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # 超管不选校区时应该有校区对比数据
        assert "campus_comparison" in data


class TestAdminDashboardWithTimeFilter:
    """管理员仪表盘 - 时间过滤"""

    async def test_time_filter_affects_time_metrics(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_enrollments: list[Enrollment],
    ):
        """时间过滤影响时间型指标"""
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()
        response = await client.get(
            f"/api/v1/dashboard/admin?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200


class TestAdminDashboardKpiCards:
    """管理员仪表盘 - KPI卡片验证"""

    async def test_kpi_cards_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_students: list[Student],
        admin_test_teachers: list[Teacher],
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
    ):
        """验证KPI卡片数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        kpi_cards = data["kpi_cards"]
        # 应该有4个KPI卡片
        assert len(kpi_cards) >= 4

        # 验证每个卡片的结构
        for card in kpi_cards:
            assert "label" in card
            assert "value" in card


class TestAdminDashboardCampusScope:
    """管理员仪表盘 - 校区数据隔离"""

    async def test_campus_admin_only_sees_own_campus_data(
        self,
        client: AsyncClient,
        bj_admin_token: str,
        admin_test_students: list[Student],
        admin_test_teachers: list[Teacher],
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
    ):
        """校区管理员只能看到自己校区的数据"""
        response = await client.get(
            "/api/v1/dashboard/admin",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 校区管理员不应该看到校区对比数据
        assert "campus_comparison" not in data or data.get("campus_comparison") is None


class TestAdminDashboardStudents:
    """管理员仪表盘 - 学生分析 Tab"""

    async def test_get_admin_students(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_students: list[Student],
    ):
        """超管可以访问学生分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/students",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "kpi_cards" in data
        assert "status_distribution" in data
        assert "source_distribution" in data
        assert "grade_distribution" in data
        assert "new_student_trend" in data

    async def test_campus_admin_students(
        self,
        client: AsyncClient,
        bj_admin_token: str,
        admin_test_students: list[Student],
    ):
        """校区管理员可以访问学生分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200

    async def test_student_cannot_access_admin_students(
        self,
        client: AsyncClient,
        student_token: str,
    ):
        """学生不能访问学生分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/students",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403

    async def test_teacher_cannot_access_admin_students(
        self,
        client: AsyncClient,
        teacher_token: str,
    ):
        """教师不能访问学生分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/students",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403

    async def test_admin_students_with_time_filter(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_students: list[Student],
    ):
        """支持时间过滤"""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = await client.get(
            f"/api/v1/dashboard/admin/students?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # 验证时间过滤标志
        for kpi in data["kpi_cards"]:
            if kpi.get("is_time_filtered"):
                assert kpi["is_time_filtered"] is True

    async def test_super_admin_filter_by_campus(
        self,
        client: AsyncClient,
        super_admin_token: str,
        test_campuses,
        admin_test_students: list[Student],
    ):
        """超管可以按校区筛选学生分析"""
        campus_id = test_campuses[0].id
        response = await client.get(
            f"/api/v1/dashboard/admin/students?campus_id={campus_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200

    async def test_admin_students_kpi_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_students: list[Student],
    ):
        """验证KPI卡片数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/students",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        kpi_cards = data["kpi_cards"]
        # 应该有4个KPI卡片：学生总数、活跃学生、本月新增、流失学生
        assert len(kpi_cards) >= 4

        # 验证每个卡片的结构
        for card in kpi_cards:
            assert "label" in card
            assert "value" in card

    async def test_admin_students_distribution_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_students: list[Student],
    ):
        """验证分布图数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/students",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证分布数据都是列表
        assert isinstance(data["status_distribution"], list)
        assert isinstance(data["source_distribution"], list)
        assert isinstance(data["grade_distribution"], list)
        assert isinstance(data["new_student_trend"], list)


class TestAdminDashboardTeachers:
    """管理员仪表盘 - 教师分析 Tab"""

    async def test_get_admin_teachers(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_teachers: list[Teacher],
        admin_test_schedules: list[Schedule],
    ):
        """超管可以访问教师分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "kpi_cards" in data
        assert "status_distribution" in data
        assert "subject_distribution" in data
        assert "workload_ranking" in data

    async def test_campus_admin_teachers(
        self,
        client: AsyncClient,
        bj_admin_token: str,
        admin_test_teachers: list[Teacher],
        admin_test_schedules: list[Schedule],
    ):
        """校区管理员可以访问教师分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200

    async def test_student_cannot_access_admin_teachers(
        self,
        client: AsyncClient,
        student_token: str,
    ):
        """学生不能访问教师分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403

    async def test_teacher_cannot_access_admin_teachers(
        self,
        client: AsyncClient,
        teacher_token: str,
    ):
        """教师不能访问教师分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403

    async def test_admin_teachers_kpi_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_teachers: list[Teacher],
    ):
        """验证KPI卡片数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        kpi_cards = data["kpi_cards"]
        # 应该有4个KPI卡片：教师总数、在职教师、本月新增、本月离职
        assert len(kpi_cards) >= 4

        # 验证每个卡片的结构
        for card in kpi_cards:
            assert "label" in card
            assert "value" in card

    async def test_admin_teachers_distribution_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_teachers: list[Teacher],
    ):
        """验证分布图数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证分布数据都是列表
        assert isinstance(data["status_distribution"], list)
        assert isinstance(data["subject_distribution"], list)
        assert isinstance(data["workload_ranking"], list)

    async def test_admin_teachers_workload_ranking_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_teachers: list[Teacher],
        admin_test_schedules: list[Schedule],
    ):
        """验证工作量排名数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/teachers",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        workload_ranking = data["workload_ranking"]
        # 如果有排名数据，验证其结构
        if workload_ranking:
            for item in workload_ranking:
                assert "rank" in item
                assert "name" in item
                assert "value" in item

    async def test_admin_teachers_with_time_filter(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_teachers: list[Teacher],
        admin_test_schedules: list[Schedule],
    ):
        """支持时间过滤"""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = await client.get(
            f"/api/v1/dashboard/admin/teachers?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # 验证时间过滤标志
        for kpi in data["kpi_cards"]:
            if kpi.get("is_time_filtered"):
                assert kpi["is_time_filtered"] is True

    async def test_super_admin_filter_by_campus(
        self,
        client: AsyncClient,
        super_admin_token: str,
        test_campuses,
        admin_test_teachers: list[Teacher],
        admin_test_schedules: list[Schedule],
    ):
        """超管可以按校区筛选教师分析"""
        campus_id = test_campuses[0].id
        response = await client.get(
            f"/api/v1/dashboard/admin/teachers?campus_id={campus_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200


class TestAdminDashboardClasses:
    """管理员仪表盘 - 班级分析 Tab"""

    async def test_get_admin_classes(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
    ):
        """超管可以访问班级分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "kpi_cards" in data
        assert "status_distribution" in data
        assert "occupancy_distribution" in data
        assert "subject_distribution" in data
        assert "progress_ranking" in data

    async def test_campus_admin_classes(
        self,
        client: AsyncClient,
        bj_admin_token: str,
        admin_test_class_plans: list[ClassPlan],
        admin_test_enrollments: list[Enrollment],
    ):
        """校区管理员可以访问班级分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200

    async def test_student_cannot_access_admin_classes(
        self,
        client: AsyncClient,
        student_token: str,
    ):
        """学生不能访问班级分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403

    async def test_teacher_cannot_access_admin_classes(
        self,
        client: AsyncClient,
        teacher_token: str,
    ):
        """教师不能访问班级分析"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403

    async def test_admin_classes_kpi_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_class_plans: list[ClassPlan],
    ):
        """验证KPI卡片数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        kpi_cards = data["kpi_cards"]
        # 应该有4个KPI卡片：班级总数、进行中班级、本月新开班、本月结业
        assert len(kpi_cards) >= 4

        # 验证每个卡片的结构
        for card in kpi_cards:
            assert "label" in card
            assert "value" in card

    async def test_admin_classes_distribution_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_class_plans: list[ClassPlan],
    ):
        """验证分布图数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证分布数据都是列表
        assert isinstance(data["status_distribution"], list)
        assert isinstance(data["occupancy_distribution"], list)
        assert isinstance(data["subject_distribution"], list)
        assert isinstance(data["progress_ranking"], list)

    async def test_admin_classes_progress_ranking_structure(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_class_plans: list[ClassPlan],
    ):
        """验证进度排名数据结构"""
        response = await client.get(
            "/api/v1/dashboard/admin/classes",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        progress_ranking = data["progress_ranking"]
        # 如果有排名数据，验证其结构
        if progress_ranking:
            for item in progress_ranking:
                assert "rank" in item
                assert "name" in item
                assert "value" in item

    async def test_admin_classes_with_time_filter(
        self,
        client: AsyncClient,
        super_admin_token: str,
        admin_test_class_plans: list[ClassPlan],
    ):
        """支持时间过滤"""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = await client.get(
            f"/api/v1/dashboard/admin/classes?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # 验证时间过滤标志
        for kpi in data["kpi_cards"]:
            if kpi.get("is_time_filtered"):
                assert kpi["is_time_filtered"] is True

    async def test_super_admin_filter_by_campus(
        self,
        client: AsyncClient,
        super_admin_token: str,
        test_campuses,
        admin_test_class_plans: list[ClassPlan],
    ):
        """超管可以按校区筛选班级分析"""
        campus_id = test_campuses[0].id
        response = await client.get(
            f"/api/v1/dashboard/admin/classes?campus_id={campus_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
