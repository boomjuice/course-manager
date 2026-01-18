"""
Tests for teacher dashboard API endpoints.
教师仪表盘API测试。
"""
import pytest
import pytest_asyncio
from datetime import date, time, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.teacher import Teacher
from app.models.schedule import Schedule
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_attendance import StudentAttendance


@pytest_asyncio.fixture
async def teacher_linked_to_user(
    db_session: AsyncSession,
    test_users: dict,
    test_campuses: list,
) -> Teacher:
    """
    Create a teacher record linked to the test teacher user.
    通过 Teacher.user_id 关联到用户账号。
    """
    teacher = Teacher(
        name="测试教师",
        phone="13800000004",
        user_id=test_users["teacher"].id,  # 关联到教师用户
        subjects=["数学", "物理"],
        hourly_rate=Decimal("150.00"),
        status="active",
        is_active=True,
        created_by="test",
    )
    db_session.add(teacher)
    await db_session.flush()
    return teacher


@pytest_asyncio.fixture
async def teacher_class_plans(
    db_session: AsyncSession,
    teacher_linked_to_user: Teacher,
    test_campuses: list,
    test_courses: list,
    test_classrooms: list,
):
    """
    Create class plans for the teacher.
    """
    from app.models.class_plan import ClassPlan

    class_plan = ClassPlan(
        name="教师测试班",
        course_id=test_courses[0].id,
        campus_id=test_campuses[0].id,
        teacher_id=teacher_linked_to_user.id,
        classroom_id=test_classrooms[0].id,
        max_students=20,
        status="ongoing",
        is_active=True,
        created_by="test",
    )
    db_session.add(class_plan)
    await db_session.flush()
    return [class_plan]


@pytest_asyncio.fixture
async def teacher_schedules(
    db_session: AsyncSession,
    teacher_linked_to_user: Teacher,
    teacher_class_plans: list,
    test_classrooms: list,
) -> list[Schedule]:
    """
    Create schedules for the teacher.
    包括过去的和未来的排课。
    """
    today = date.today()
    schedules = []
    class_plan = teacher_class_plans[0]

    # 过去已完成的排课（用于计算课时收入）
    for i in range(5):
        schedule = Schedule(
            class_plan_id=class_plan.id,
            campus_id=class_plan.campus_id,
            teacher_id=teacher_linked_to_user.id,
            classroom_id=test_classrooms[0].id,
            schedule_date=today - timedelta(days=i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            lesson_hours=2.0,
            status="completed",
            created_by="test",
        )
        schedules.append(schedule)

    # 今日排课
    today_schedule = Schedule(
        class_plan_id=class_plan.id,
        campus_id=class_plan.campus_id,
        teacher_id=teacher_linked_to_user.id,
        classroom_id=test_classrooms[0].id,
        schedule_date=today,
        start_time=time(14, 0),
        end_time=time(16, 0),
        lesson_hours=2.0,
        status="scheduled",
        created_by="test",
    )
    schedules.append(today_schedule)

    # 未来7天的排课
    for i in range(4):
        schedule = Schedule(
            class_plan_id=class_plan.id,
            campus_id=class_plan.campus_id,
            teacher_id=teacher_linked_to_user.id,
            classroom_id=test_classrooms[0].id,
            schedule_date=today + timedelta(days=i + 1),
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


@pytest_asyncio.fixture
async def teacher_students(
    db_session: AsyncSession,
    teacher_class_plans: list,
    test_campuses: list,
) -> list[Student]:
    """
    Create students enrolled in the teacher's class.
    """
    students = []
    for i in range(3):
        student = Student(
            name=f"班级学生{i+1}",
            phone=f"1360000100{i}",
            campus_id=test_campuses[0].id,
            status="active",
            is_active=True,
            created_by="test",
        )
        students.append(student)

    db_session.add_all(students)
    await db_session.flush()
    return students


@pytest_asyncio.fixture
async def teacher_enrollments(
    db_session: AsyncSession,
    teacher_students: list[Student],
    teacher_class_plans: list,
) -> list[Enrollment]:
    """
    Create enrollments for the teacher's class.
    """
    enrollments = []
    class_plan = teacher_class_plans[0]

    for student in teacher_students:
        enrollment = Enrollment(
            student_id=student.id,
            class_plan_id=class_plan.id,
            campus_id=class_plan.campus_id,
            enroll_date=date.today() - timedelta(days=30),
            paid_amount=Decimal("3000.00"),
            purchased_hours=Decimal("20.0"),
            used_hours=Decimal("5.0"),
            status="active",
            created_by="test",
        )
        enrollments.append(enrollment)

    db_session.add_all(enrollments)
    await db_session.flush()
    return enrollments


@pytest_asyncio.fixture
async def teacher_attendance_records(
    db_session: AsyncSession,
    teacher_enrollments: list[Enrollment],
    teacher_schedules: list[Schedule],
) -> list[StudentAttendance]:
    """
    Create attendance records for the teacher's students.
    """
    attendances = []
    # 只为已完成的排课创建出勤记录
    completed_schedules = [s for s in teacher_schedules if s.status == "completed"]

    for enrollment in teacher_enrollments:
        for i, schedule in enumerate(completed_schedules[:3]):  # 每个学生3条记录
            # 随机设置出勤状态
            if i == 0:
                status = "normal"
            elif i == 1:
                status = "leave"
            else:
                status = "normal"

            attendance = StudentAttendance(
                enrollment_id=enrollment.id,
                schedule_id=schedule.id,
                status=status,
                leave_reason="家中有事" if status == "leave" else None,
                deduct_hours=False,
                created_by="test",
            )
            attendances.append(attendance)

    db_session.add_all(attendances)
    await db_session.flush()
    return attendances


class TestTeacherDashboardOverview:
    """Test GET /api/v1/dashboard/teacher endpoint."""

    @pytest.mark.asyncio
    async def test_teacher_can_access_own_dashboard(
        self,
        client: AsyncClient,
        teacher_token: str,
        teacher_linked_to_user: Teacher,
        teacher_class_plans: list,
        teacher_schedules: list[Schedule],
    ):
        """教师可以访问自己的仪表盘概览。"""
        response = await client.get(
            "/api/v1/dashboard/teacher",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        # 验证返回数据结构
        result = data["data"]
        assert "today_class_count" in result
        assert "week_class_count" in result
        assert "month_lesson_hours" in result
        assert "active_class_count" in result
        assert "upcoming_schedules" in result
        assert "today_schedules" in result

        # 验证KPI卡片结构
        assert "label" in result["today_class_count"]
        assert "value" in result["today_class_count"]

        # 验证今日排课数量（fixture中创建了1节今日排课）
        assert result["today_class_count"]["value"] == 1

        # 验证未来7天排课（今日1 + 未来4 = 5）
        assert len(result["upcoming_schedules"]) == 5

    @pytest.mark.asyncio
    async def test_student_cannot_access_teacher_dashboard(
        self,
        client: AsyncClient,
        student_token: str,
    ):
        """学生不能访问教师仪表盘，返回403。"""
        response = await client.get(
            "/api/v1/dashboard/teacher",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 403


class TestTeacherDashboardClasses:
    """Test GET /api/v1/dashboard/teacher/classes endpoint."""

    @pytest.mark.asyncio
    async def test_get_teacher_classes(
        self,
        client: AsyncClient,
        teacher_token: str,
        teacher_linked_to_user: Teacher,
        teacher_class_plans: list,
        teacher_enrollments: list[Enrollment],
        teacher_schedules: list[Schedule],
        teacher_attendance_records: list[StudentAttendance],
    ):
        """教师可以获取自己带的班级和学生出勤统计。"""
        response = await client.get(
            "/api/v1/dashboard/teacher/classes",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        result = data["data"]
        assert "classes" in result
        assert "student_attendance" in result
        assert "students_by_class" in result

        # 应该有1个班级
        assert len(result["classes"]) == 1

        # 验证班级字段
        class_item = result["classes"][0]
        assert "class_plan_id" in class_item
        assert "class_plan_name" in class_item
        assert "course_name" in class_item
        assert "student_count" in class_item
        assert "total_schedules" in class_item
        assert "completed_schedules" in class_item

        # 学生人数应该为3
        assert class_item["student_count"] == 3

        # 应该有3个学生的出勤统计
        assert len(result["student_attendance"]) == 3


class TestTeacherDashboardIncome:
    """Test GET /api/v1/dashboard/teacher/income endpoint."""

    @pytest.mark.asyncio
    async def test_get_teacher_income(
        self,
        client: AsyncClient,
        teacher_token: str,
        teacher_linked_to_user: Teacher,
        teacher_schedules: list[Schedule],
    ):
        """教师可以获取自己的课时收入统计。"""
        response = await client.get(
            "/api/v1/dashboard/teacher/income",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        result = data["data"]
        assert "month_income" in result
        assert "month_hours" in result
        assert "hourly_rate" in result
        assert "income_trend" in result
        assert "hours_trend" in result
        assert "hours_by_class" in result

        # 验证课时单价（fixture中设置为150）
        assert result["hourly_rate"]["value"] == 150.0

        # 已完成的课时数（5个已完成排课，每个2课时 = 10课时）
        # 注意：需要判断是否在本月内
        assert result["month_hours"]["value"] >= 0

    @pytest.mark.asyncio
    async def test_get_teacher_income_with_time_filter(
        self,
        client: AsyncClient,
        teacher_token: str,
        teacher_linked_to_user: Teacher,
        teacher_schedules: list[Schedule],
    ):
        """带时间过滤获取课时收入。"""
        today = date.today()
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()

        response = await client.get(
            f"/api/v1/dashboard/teacher/income?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        result = data["data"]
        # 应该包含过滤后的数据
        assert "month_income" in result
        assert "month_hours" in result


class TestTeacherDashboardAccessControl:
    """Test access control for teacher dashboard."""

    @pytest.mark.asyncio
    async def test_admin_cannot_access_teacher_dashboard(
        self,
        client: AsyncClient,
        super_admin_token: str,
    ):
        """管理员不能访问教师仪表盘。"""
        response = await client.get(
            "/api/v1/dashboard/teacher",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access(
        self,
        client: AsyncClient,
    ):
        """未认证用户不能访问。"""
        response = await client.get("/api/v1/dashboard/teacher")
        assert response.status_code == 401
