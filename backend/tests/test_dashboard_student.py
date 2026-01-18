"""
Tests for student dashboard API endpoints.
学生仪表盘API测试。
"""
import pytest
import pytest_asyncio
from datetime import date, time, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule
from app.models.student_attendance import StudentAttendance
from app.models.lesson_record import LessonRecord


@pytest_asyncio.fixture
async def student_linked_to_user(
    db_session: AsyncSession,
    test_users: dict,
    test_campuses: list,
) -> Student:
    """
    Create a student record linked to the test student user.
    通过 Student.user_id 关联到用户账号。
    """
    student = Student(
        name="测试学生",
        phone="13700000001",
        user_id=test_users["student"].id,  # 关联到学生用户
        campus_id=test_campuses[0].id,
        status="active",
        total_hours=Decimal("100.0"),
        remaining_hours=Decimal("50.0"),
        is_active=True,
        created_by="test",
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest_asyncio.fixture
async def student_enrollment(
    db_session: AsyncSession,
    student_linked_to_user: Student,
    test_class_plans: list,
) -> Enrollment:
    """
    Create an enrollment for the student.
    """
    enrollment = Enrollment(
        student_id=student_linked_to_user.id,
        class_plan_id=test_class_plans[0].id,
        campus_id=test_class_plans[0].campus_id,
        enroll_date=date.today() - timedelta(days=30),
        paid_amount=Decimal("3000.00"),
        purchased_hours=Decimal("20.0"),
        used_hours=Decimal("5.0"),
        status="active",
        created_by="test",
    )
    db_session.add(enrollment)
    await db_session.flush()
    return enrollment


@pytest_asyncio.fixture
async def student_schedules(
    db_session: AsyncSession,
    test_class_plans: list,
    test_teachers: list,
    test_classrooms: list,
) -> list[Schedule]:
    """
    Create schedules for the student's class plan.
    包括过去的和未来的排课。
    """
    today = date.today()
    schedules = []

    # 过去的排课
    for i in range(3):
        schedule = Schedule(
            class_plan_id=test_class_plans[0].id,
            campus_id=test_class_plans[0].campus_id,
            teacher_id=test_teachers[0].id,
            classroom_id=test_classrooms[0].id,
            schedule_date=today - timedelta(days=i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            lesson_hours=2.0,
            status="completed",
            created_by="test",
        )
        schedules.append(schedule)

    # 未来7天的排课
    for i in range(5):
        schedule = Schedule(
            class_plan_id=test_class_plans[0].id,
            campus_id=test_class_plans[0].campus_id,
            teacher_id=test_teachers[0].id,
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
async def student_attendance_records(
    db_session: AsyncSession,
    student_enrollment: Enrollment,
    student_schedules: list[Schedule],
) -> list[StudentAttendance]:
    """
    Create attendance records for the student.
    """
    attendances = []
    # 只为已完成的排课创建出勤记录
    completed_schedules = [s for s in student_schedules if s.status == "completed"]

    for i, schedule in enumerate(completed_schedules):
        status = "normal" if i < 2 else "leave"  # 2次正常，1次请假
        attendance = StudentAttendance(
            enrollment_id=student_enrollment.id,
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


@pytest_asyncio.fixture
async def student_lesson_records(
    db_session: AsyncSession,
    student_enrollment: Enrollment,
    student_schedules: list[Schedule],
) -> list[LessonRecord]:
    """
    Create lesson consumption records for the student.
    """
    records = []
    # 只为已完成的排课创建课时消耗记录
    completed_schedules = [s for s in student_schedules if s.status == "completed"]

    for schedule in completed_schedules:
        record = LessonRecord(
            enrollment_id=student_enrollment.id,
            schedule_id=schedule.id,
            record_date=schedule.schedule_date,
            hours=Decimal("2.0"),
            type="schedule",
            created_by="test",
        )
        records.append(record)

    db_session.add_all(records)
    await db_session.flush()
    return records


class TestStudentDashboardOverview:
    """Test GET /api/v1/dashboard/student endpoint."""

    @pytest.mark.asyncio
    async def test_student_can_access_own_dashboard(
        self,
        client: AsyncClient,
        student_token: str,
        student_linked_to_user: Student,
        student_enrollment: Enrollment,
        student_schedules: list[Schedule],
    ):
        """学生可以访问自己的仪表盘概览。"""
        response = await client.get(
            "/api/v1/dashboard/student",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        # 验证返回数据结构
        result = data["data"]
        assert "total_remaining_hours" in result
        assert "upcoming_class_count" in result
        assert "attendance_rate" in result
        assert "active_enrollment_count" in result
        assert "upcoming_schedules" in result

        # 验证KPI卡片结构
        assert "label" in result["total_remaining_hours"]
        assert "value" in result["total_remaining_hours"]

    @pytest.mark.asyncio
    async def test_admin_cannot_access_student_dashboard(
        self,
        client: AsyncClient,
        super_admin_token: str,
    ):
        """管理员不能访问学生仪表盘，返回403。"""
        response = await client.get(
            "/api/v1/dashboard/student",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_student_dashboard(
        self,
        client: AsyncClient,
        teacher_token: str,
    ):
        """教师不能访问学生仪表盘，返回403。"""
        response = await client.get(
            "/api/v1/dashboard/student",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 403


class TestStudentDashboardCourses:
    """Test GET /api/v1/dashboard/student/courses endpoint."""

    @pytest.mark.asyncio
    async def test_get_student_courses(
        self,
        client: AsyncClient,
        student_token: str,
        student_linked_to_user: Student,
        student_enrollment: Enrollment,
    ):
        """学生可以获取自己报名的班级列表。"""
        response = await client.get(
            "/api/v1/dashboard/student/courses",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        result = data["data"]
        assert "enrollments" in result
        # 应该有1条报名记录
        assert len(result["enrollments"]) == 1

        # 验证报名记录字段
        enrollment = result["enrollments"][0]
        assert "enrollment_id" in enrollment
        assert "class_plan_id" in enrollment
        assert "class_plan_name" in enrollment
        assert "course_name" in enrollment
        assert "total_hours" in enrollment
        assert "remaining_hours" in enrollment


class TestStudentDashboardRecords:
    """Test GET /api/v1/dashboard/student/records endpoint."""

    @pytest.mark.asyncio
    async def test_get_student_records(
        self,
        client: AsyncClient,
        student_token: str,
        student_linked_to_user: Student,
        student_enrollment: Enrollment,
        student_attendance_records: list[StudentAttendance],
        student_lesson_records: list[LessonRecord],
    ):
        """学生可以获取自己的学习记录。"""
        response = await client.get(
            "/api/v1/dashboard/student/records",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        result = data["data"]
        assert "attendance_summary" in result
        assert "recent_attendance" in result
        assert "lesson_records" in result

        # 验证出勤统计
        attendance_summary = result["attendance_summary"]
        assert "total" in attendance_summary
        assert "normal" in attendance_summary
        assert "leave" in attendance_summary
        assert "absent" in attendance_summary

        # 应该有3条出勤记录（2正常+1请假）
        assert len(result["recent_attendance"]) == 3

    @pytest.mark.asyncio
    async def test_get_student_records_with_time_filter(
        self,
        client: AsyncClient,
        student_token: str,
        student_linked_to_user: Student,
        student_enrollment: Enrollment,
        student_attendance_records: list[StudentAttendance],
        student_lesson_records: list[LessonRecord],
    ):
        """带时间过滤获取学习记录。"""
        today = date.today()
        start_date = (today - timedelta(days=2)).isoformat()
        end_date = today.isoformat()

        response = await client.get(
            f"/api/v1/dashboard/student/records?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

        result = data["data"]
        # 时间过滤后，课时消耗记录数应该减少
        # 因为只有2天范围内的记录
        assert "lesson_records" in result
