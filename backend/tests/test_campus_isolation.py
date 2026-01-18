"""
Campus isolation unit tests.
校区数据隔离单元测试：测试Student/Course/Schedule的校区过滤逻辑。
"""
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import date, time

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campus import Campus
from app.models.student import Student
from app.models.course import Course
from app.models.schedule import Schedule
from app.models.class_plan import ClassPlan
from app.models.user import User
from app.services.student_service import StudentService
from app.services.course_service import CourseService
from app.services.schedule_service import ScheduleService


class TestStudentCampusIsolation:
    """测试学生数据的校区隔离"""

    @pytest_asyncio.fixture
    async def student_service(self, db_session: AsyncSession) -> StudentService:
        """创建学生服务实例"""
        return StudentService(db_session)

    @pytest.mark.asyncio
    async def test_list_students_filtered_by_campus(
        self,
        client: AsyncClient,
        test_students: list[Student],
        test_users: dict[str, User],
        bj_admin_token: str,
        sh_admin_token: str
    ):
        """测试学生列表按校区过滤"""
        # 北京管理员只能看到北京校区的学生
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 只应该看到北京校区的学生
        for student in data["data"]["items"]:
            bj_campus_id = test_users["bj_campus_admin"].campus_id
            assert student["campus_id"] == bj_campus_id

        # 上海管理员只能看到上海校区的学生
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {sh_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 只应该看到上海校区的学生
        for student in data["data"]["items"]:
            sh_campus_id = test_users["sh_campus_admin"].campus_id
            assert student["campus_id"] == sh_campus_id

    @pytest.mark.asyncio
    async def test_super_admin_sees_selected_campus_students(
        self,
        client: AsyncClient,
        test_students: list[Student],
        test_users: dict[str, User],
        test_campuses: list[Campus],
        super_admin_token: str
    ):
        """
        超级管理员选择校区后只能看到该校区的学生。
        新架构下，超管登录时需选择校区，数据按选中校区过滤。
        """
        response = await client.get(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 超管token默认选择北京校区，只应看到北京校区的学生
        bj_campus_id = test_campuses[0].id
        for student in data["data"]["items"]:
            assert student["campus_id"] == bj_campus_id

    @pytest.mark.asyncio
    async def test_create_student_in_own_campus(
        self,
        client: AsyncClient,
        test_campuses: list[Campus],
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """校区管理员只能在自己校区创建学生"""
        bj_campus = test_campuses[0]

        response = await client.post(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "name": "北京新学生",
                "phone": "13800138001",
                "campus_id": bj_campus.id,
                "status": "active"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["campus_id"] == bj_campus.id

    @pytest.mark.asyncio
    async def test_create_student_in_other_campus_forbidden(
        self,
        client: AsyncClient,
        test_campuses: list[Campus],
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """校区管理员不能在其他校区创建学生"""
        sh_campus = test_campuses[1]  # 上海校区

        response = await client.post(
            "/api/v1/students",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "name": "跨校区学生",
                "phone": "13800138002",
                "campus_id": sh_campus.id,  # 尝试创建在上海校区
                "status": "active"
            }
        )
        # 应该被拒绝
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_student_detail_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_students: list[Student],
        bj_admin_token: str
    ):
        """校区管理员不能获取其他校区学生的详情"""
        sh_student = test_students[1]  # 上海的学生

        response = await client.get(
            f"/api/v1/students/{sh_student.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        # 应该返回403或404
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_update_student_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_students: list[Student],
        bj_admin_token: str
    ):
        """校区管理员不能更新其他校区的学生"""
        sh_student = test_students[1]  # 上海的学生

        response = await client.put(
            f"/api/v1/students/{sh_student.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={"name": "尝试修改上海学生"}
        )
        # 应该返回403或404
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_delete_student_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_students: list[Student],
        bj_admin_token: str
    ):
        """校区管理员不能删除其他校区的学生"""
        sh_student = test_students[1]  # 上海的学生

        response = await client.delete(
            f"/api/v1/students/{sh_student.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        # 应该返回403或404
        assert response.status_code in [403, 404]


class TestCourseCampusIsolation:
    """测试课程数据的校区隔离"""

    @pytest_asyncio.fixture
    async def course_service(self, db_session: AsyncSession) -> CourseService:
        """创建课程服务实例"""
        return CourseService(db_session)

    @pytest.mark.asyncio
    async def test_list_courses_filtered_by_campus(
        self,
        client: AsyncClient,
        test_courses: list[Course],
        test_users: dict[str, User],
        bj_admin_token: str,
        sh_admin_token: str
    ):
        """测试课程列表按校区过滤"""
        # 北京管理员只能看到北京校区的课程
        response = await client.get(
            "/api/v1/courses",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for course in data["data"]["items"]:
            bj_campus_id = test_users["bj_campus_admin"].campus_id
            assert course["campus_id"] == bj_campus_id

    @pytest.mark.asyncio
    async def test_create_course_in_own_campus(
        self,
        client: AsyncClient,
        test_campuses: list[Campus],
        bj_admin_token: str
    ):
        """校区管理员只能在自己校区创建课程"""
        bj_campus = test_campuses[0]

        response = await client.post(
            "/api/v1/courses",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "name": "北京新课程",
                "code": "BJ-NEW-001",
                "campus_id": bj_campus.id,
                "subject": "测试科目",
                "unit_price": "50.00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["campus_id"] == bj_campus.id

    @pytest.mark.asyncio
    async def test_create_course_in_other_campus_forbidden(
        self,
        client: AsyncClient,
        test_campuses: list[Campus],
        bj_admin_token: str
    ):
        """校区管理员不能在其他校区创建课程"""
        sh_campus = test_campuses[1]

        response = await client.post(
            "/api/v1/courses",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "name": "跨校区课程",
                "code": "SH-CROSS-001",
                "campus_id": sh_campus.id,  # 尝试创建在上海校区
                "subject": "测试科目",
                "unit_price": "50.00"
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_course_detail_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_courses: list[Course],
        bj_admin_token: str
    ):
        """校区管理员不能获取其他校区课程的详情"""
        sh_course = test_courses[1]  # 上海的课程

        response = await client.get(
            f"/api/v1/courses/{sh_course.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code in [403, 404]


class TestScheduleCampusIsolation:
    """测试排课数据的校区隔离"""

    @pytest_asyncio.fixture
    async def schedule_service(self, db_session: AsyncSession) -> ScheduleService:
        """创建排课服务实例"""
        return ScheduleService(db_session)

    @pytest_asyncio.fixture
    async def test_schedules(
        self,
        db_session: AsyncSession,
        test_class_plans: list[ClassPlan],
        test_campuses: list[Campus]
    ) -> list[Schedule]:
        """创建测试排课数据"""
        # 北京校区的排课
        schedule_bj = Schedule(
            class_plan_id=test_class_plans[0].id,
            campus_id=test_campuses[0].id,
            schedule_date=date(2024, 3, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            lesson_hours=2.0,
            status="pending",
            created_by="test"
        )
        # 上海校区的排课
        schedule_sh = Schedule(
            class_plan_id=test_class_plans[1].id,
            campus_id=test_campuses[1].id,
            schedule_date=date(2024, 3, 1),
            start_time=time(14, 0),
            end_time=time(16, 0),
            lesson_hours=2.0,
            status="pending",
            created_by="test"
        )
        db_session.add_all([schedule_bj, schedule_sh])
        await db_session.flush()
        return [schedule_bj, schedule_sh]

    @pytest.mark.asyncio
    async def test_list_schedules_filtered_by_campus(
        self,
        client: AsyncClient,
        test_schedules: list[Schedule],
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """测试排课列表按校区过滤"""
        response = await client.get(
            "/api/v1/schedules",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 北京管理员只能看到北京校区的排课
        bj_campus_id = test_users["bj_campus_admin"].campus_id
        for schedule in data["data"]["items"]:
            assert schedule["campus_id"] == bj_campus_id

    @pytest.mark.asyncio
    async def test_create_schedule_auto_assigns_campus(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_campuses: list[Campus],
        bj_admin_token: str
    ):
        """测试创建排课时自动从ClassPlan获取campus_id"""
        bj_class_plan = test_class_plans[0]  # 北京校区的班级

        response = await client.post(
            "/api/v1/schedules",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": bj_class_plan.id,
                "schedule_date": "2024-03-15",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "lesson_hours": 2.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        # campus_id应该自动从ClassPlan获取
        assert data["data"]["campus_id"] == test_campuses[0].id

    @pytest.mark.asyncio
    async def test_create_schedule_for_other_campus_class_plan_forbidden(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        bj_admin_token: str
    ):
        """校区管理员不能为其他校区的班级创建排课"""
        sh_class_plan = test_class_plans[1]  # 上海校区的班级

        response = await client.post(
            "/api/v1/schedules",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": sh_class_plan.id,
                "schedule_date": "2024-03-15",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "lesson_hours": 2.0
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_schedule_detail_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_schedules: list[Schedule],
        bj_admin_token: str
    ):
        """校区管理员不能获取其他校区排课的详情"""
        sh_schedule = test_schedules[1]  # 上海的排课

        response = await client.get(
            f"/api/v1/schedules/{sh_schedule.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_update_schedule_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_schedules: list[Schedule],
        bj_admin_token: str
    ):
        """校区管理员不能更新其他校区的排课"""
        sh_schedule = test_schedules[1]  # 上海的排课

        response = await client.put(
            f"/api/v1/schedules/{sh_schedule.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={"lesson_hours": 3.0}
        )
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_delete_schedule_cross_campus_forbidden(
        self,
        client: AsyncClient,
        test_schedules: list[Schedule],
        bj_admin_token: str
    ):
        """校区管理员不能删除其他校区的排课"""
        sh_schedule = test_schedules[1]  # 上海的排课

        response = await client.delete(
            f"/api/v1/schedules/{sh_schedule.id}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code in [403, 404]


class TestCalendarCampusFilter:
    """测试日历视图的校区过滤"""

    @pytest_asyncio.fixture
    async def test_schedules(
        self,
        db_session: AsyncSession,
        test_class_plans: list[ClassPlan],
        test_campuses: list[Campus]
    ) -> list[Schedule]:
        """创建测试排课数据"""
        schedules = []
        # 北京校区3个排课
        for i in range(3):
            schedule = Schedule(
                class_plan_id=test_class_plans[0].id,
                campus_id=test_campuses[0].id,
                schedule_date=date(2024, 3, i + 1),
                start_time=time(9, 0),
                end_time=time(11, 0),
                lesson_hours=2.0,
                status="pending",
                created_by="test"
            )
            schedules.append(schedule)

        # 上海校区2个排课
        for i in range(2):
            schedule = Schedule(
                class_plan_id=test_class_plans[1].id,
                campus_id=test_campuses[1].id,
                schedule_date=date(2024, 3, i + 1),
                start_time=time(14, 0),
                end_time=time(16, 0),
                lesson_hours=2.0,
                status="pending",
                created_by="test"
            )
            schedules.append(schedule)

        db_session.add_all(schedules)
        await db_session.flush()
        return schedules

    @pytest.mark.asyncio
    async def test_calendar_events_filtered_by_campus(
        self,
        client: AsyncClient,
        test_schedules: list[Schedule],
        test_users: dict[str, User],
        bj_admin_token: str
    ):
        """测试日历事件按校区过滤"""
        response = await client.get(
            "/api/v1/schedules/calendar",
            params={"start_date": "2024-03-01", "end_date": "2024-03-31"},
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200
        events = response.json()["data"]["items"]
        # 北京管理员只能看到北京校区的3个排课
        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_super_admin_sees_selected_campus_calendar_events(
        self,
        client: AsyncClient,
        test_schedules: list[Schedule],
        super_admin_token: str
    ):
        """
        超级管理员选择校区后只能看到该校区的日历事件。
        新架构下，超管token默认选择北京校区。
        """
        response = await client.get(
            "/api/v1/schedules/calendar",
            params={"start_date": "2024-03-01", "end_date": "2024-03-31"},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        events = response.json()["data"]["items"]
        # 超管选择了北京校区，只能看到北京校区的3个排课
        assert len(events) == 3
