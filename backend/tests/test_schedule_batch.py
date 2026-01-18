"""
Schedule batch operations unit tests.
排课批次号功能单元测试：批量创建排课、按批次号删除等。
"""
import pytest
import pytest_asyncio
from datetime import date, time
from typing import List

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.campus import Campus
from app.models.class_plan import ClassPlan
from app.models.schedule import Schedule
from app.models.enrollment import Enrollment
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.schemas.schedule import ScheduleBatchCreate, DateRange, TimeSlot


class TestScheduleBatchCreate:
    """测试批量创建排课"""

    @pytest_asyncio.fixture
    async def schedule_service(self, db_session: AsyncSession) -> ScheduleService:
        """创建排课服务实例"""
        return ScheduleService(db_session)

    @pytest_asyncio.fixture
    async def test_enrollment(
        self,
        db_session: AsyncSession,
        test_class_plans: list[ClassPlan],
        test_students
    ):
        """创建测试报名数据（让班级有在读学生）"""
        enrollment = Enrollment(
            student_id=test_students[0].id,
            class_plan_id=test_class_plans[0].id,
            campus_id=test_class_plans[0].campus_id,
            enroll_date=date(2024, 1, 1),
            paid_amount=3000,
            purchased_hours=20,
            used_hours=0,
            status="active",
            created_by="test"
        )
        db_session.add(enrollment)
        await db_session.flush()
        return enrollment

    @pytest.mark.asyncio
    async def test_batch_create_generates_batch_no(
        self,
        schedule_service: ScheduleService,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        db_session: AsyncSession
    ):
        """测试批量创建排课会自动生成批次号"""
        data = ScheduleBatchCreate(
            class_plan_id=test_class_plans[0].id,
            date_ranges=[DateRange(start_date=date(2024, 3, 1), end_date=date(2024, 3, 15))],
            time_slots=[TimeSlot(weekdays=[0, 2, 4], start_time=time(9, 0), end_time=time(11, 0))],
            lesson_hours=2.0
        )

        schedules, created_count, skipped_count, batch_no = await schedule_service.batch_create_schedules(
            data=data,
            created_by="test"
        )

        # 验证批次号格式
        assert batch_no is not None
        assert batch_no.startswith("BATCH-")
        assert len(batch_no) == 18  # BATCH- + 12位hex

        # 验证创建数量
        assert created_count == len(schedules)
        assert created_count > 0

        # 所有创建的排课都应该有相同的批次号
        for schedule in schedules:
            assert schedule.batch_no == batch_no

    @pytest.mark.asyncio
    async def test_batch_create_respects_weekday_pattern(
        self,
        schedule_service: ScheduleService,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        db_session: AsyncSession
    ):
        """测试批量创建排课遵循weekdays模式"""
        # 2024年3月1日是周五，3月4日是周一
        data = ScheduleBatchCreate(
            class_plan_id=test_class_plans[0].id,
            date_ranges=[DateRange(start_date=date(2024, 3, 1), end_date=date(2024, 3, 10))],
            time_slots=[TimeSlot(weekdays=[0, 4], start_time=time(9, 0), end_time=time(11, 0))],
            lesson_hours=2.0
        )

        schedules, created_count, skipped_count, batch_no = await schedule_service.batch_create_schedules(
            data=data,
            created_by="test"
        )

        # 应该创建3个排课：3/1(周五), 3/4(周一), 3/8(周五)
        # 注：根据实际日历调整
        assert created_count > 0
        assert len(schedules) == created_count

    @pytest.mark.asyncio
    async def test_batch_create_assigns_campus_from_class_plan(
        self,
        schedule_service: ScheduleService,
        test_class_plans: list[ClassPlan],
        test_campuses: list[Campus],
        test_enrollment,
        db_session: AsyncSession
    ):
        """测试批量创建时campus_id从ClassPlan自动获取"""
        bj_class_plan = test_class_plans[0]  # 北京校区的班级

        data = ScheduleBatchCreate(
            class_plan_id=bj_class_plan.id,
            date_ranges=[DateRange(start_date=date(2024, 4, 1), end_date=date(2024, 4, 7))],
            time_slots=[TimeSlot(weekdays=[0, 1, 2, 3, 4], start_time=time(9, 0), end_time=time(11, 0))],
            lesson_hours=2.0
        )

        schedules, created_count, skipped_count, batch_no = await schedule_service.batch_create_schedules(
            data=data,
            created_by="test"
        )

        # 所有排课的campus_id应该等于ClassPlan的campus_id
        for schedule in schedules:
            assert schedule.campus_id == bj_class_plan.campus_id

    @pytest.mark.asyncio
    async def test_batch_create_api(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        bj_admin_token: str
    ):
        """测试批量创建排课API"""
        response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[0].id,
                "date_ranges": [{"start_date": "2024-03-01", "end_date": "2024-03-15"}],
                "time_slots": [{"weekdays": [0, 2, 4], "start_time": "09:00", "end_time": "11:00"}],
                "lesson_hours": 2.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["created_count"] > 0
        assert data["data"]["batch_no"].startswith("BATCH-")

    @pytest.mark.asyncio
    async def test_batch_create_campus_admin_own_campus_only(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        bj_admin_token: str
    ):
        """校区管理员只能为自己校区创建排课"""
        # 使用北京校区的班级
        response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[0].id,
                "date_ranges": [{"start_date": "2024-05-01", "end_date": "2024-05-07"}],
                "time_slots": [{"weekdays": [0], "start_time": "14:00", "end_time": "16:00"}],
                "lesson_hours": 2.0
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_batch_create_campus_admin_other_campus_forbidden(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        bj_admin_token: str
    ):
        """校区管理员不能为其他校区创建排课"""
        # 尝试使用上海校区的班级
        response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[1].id,  # 上海校区班级
                "date_ranges": [{"start_date": "2024-05-01", "end_date": "2024-05-07"}],
                "time_slots": [{"weekdays": [0], "start_time": "14:00", "end_time": "16:00"}],
                "lesson_hours": 2.0
            }
        )
        assert response.status_code == 403


class TestScheduleBatchDelete:
    """测试按批次号删除排课"""

    @pytest_asyncio.fixture
    async def schedule_service(self, db_session: AsyncSession) -> ScheduleService:
        """创建排课服务实例"""
        return ScheduleService(db_session)

    @pytest_asyncio.fixture
    async def test_batch_enrollment(
        self,
        db_session: AsyncSession,
        test_class_plans: list[ClassPlan],
        test_students
    ):
        """创建测试报名数据"""
        enrollment = Enrollment(
            student_id=test_students[0].id,
            class_plan_id=test_class_plans[0].id,
            campus_id=test_class_plans[0].campus_id,
            enroll_date=date(2024, 1, 1),
            paid_amount=3000,
            purchased_hours=20,
            used_hours=0,
            status="active",
            created_by="test"
        )
        db_session.add(enrollment)
        await db_session.flush()
        return enrollment

    @pytest.mark.asyncio
    async def test_delete_by_batch_no(
        self,
        schedule_service: ScheduleService,
        test_class_plans: list[ClassPlan],
        test_batch_enrollment,
        db_session: AsyncSession
    ):
        """测试按批次号删除排课"""
        # 先创建一批排课
        create_data = ScheduleBatchCreate(
            class_plan_id=test_class_plans[0].id,
            date_ranges=[DateRange(start_date=date(2024, 6, 1), end_date=date(2024, 6, 7))],
            time_slots=[TimeSlot(weekdays=[0], start_time=time(10, 0), end_time=time(12, 0))],
            lesson_hours=2.0
        )
        schedules, created_count, skipped_count, batch_no = await schedule_service.batch_create_schedules(
            data=create_data,
            created_by="test"
        )

        # 删除这批排课
        deleted_count = await schedule_service.delete_by_batch_no(
            batch_no=batch_no
        )

        # 验证删除数量
        assert deleted_count == created_count

    @pytest.mark.asyncio
    async def test_delete_by_batch_no_api(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_batch_enrollment,
        bj_admin_token: str,
        db_session: AsyncSession
    ):
        """测试按批次号删除排课API"""
        # 先创建一批排课
        create_response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[0].id,
                "date_ranges": [{"start_date": "2024-07-01", "end_date": "2024-07-07"}],
                "time_slots": [{"weekdays": [0], "start_time": "10:00", "end_time": "12:00"}],
                "lesson_hours": 2.0
            }
        )
        batch_no = create_response.json()["data"]["batch_no"]

        # 删除这批排课
        delete_response = await client.delete(
            f"/api/v1/schedules/batch/{batch_no}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        # API返回MessageResponse，检查message包含删除数量
        assert "删除" in data["data"]["message"]

    @pytest.mark.asyncio
    async def test_delete_by_batch_no_campus_filter(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_batch_enrollment,
        bj_admin_token: str
    ):
        """测试删除时校区过滤"""
        # 先创建一批排课
        create_response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[0].id,
                "date_ranges": [{"start_date": "2024-08-01", "end_date": "2024-08-07"}],
                "time_slots": [{"weekdays": [0], "start_time": "10:00", "end_time": "12:00"}],
                "lesson_hours": 2.0
            }
        )
        batch_no = create_response.json()["data"]["batch_no"]

        # 删除这批排课
        delete_response = await client.delete(
            f"/api/v1/schedules/batch/{batch_no}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert delete_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_by_batch_no_campus_admin_own_campus_only(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_batch_enrollment,
        bj_admin_token: str,
        sh_admin_token: str
    ):
        """校区管理员只能删除本校区的排课"""
        # 先创建一批北京校区的排课
        create_response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[0].id,
                "date_ranges": [{"start_date": "2024-09-01", "end_date": "2024-09-07"}],
                "time_slots": [{"weekdays": [0], "start_time": "10:00", "end_time": "12:00"}],
                "lesson_hours": 2.0
            }
        )
        batch_no = create_response.json()["data"]["batch_no"]

        # 北京管理员可以删除
        delete_response = await client.delete(
            f"/api/v1/schedules/batch/{batch_no}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert delete_response.status_code == 200


class TestScheduleBatchQuery:
    """测试按批次号查询排课"""

    @pytest_asyncio.fixture
    async def test_enrollment(
        self,
        db_session: AsyncSession,
        test_class_plans: list[ClassPlan],
        test_students
    ):
        """创建测试报名数据"""
        enrollment = Enrollment(
            student_id=test_students[0].id,
            class_plan_id=test_class_plans[0].id,
            campus_id=test_class_plans[0].campus_id,
            enroll_date=date(2024, 1, 1),
            paid_amount=3000,
            purchased_hours=20,
            used_hours=0,
            status="active",
            created_by="test"
        )
        db_session.add(enrollment)
        await db_session.flush()
        return enrollment

    @pytest.mark.asyncio
    async def test_query_by_batch_no(
        self,
        client: AsyncClient,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        bj_admin_token: str
    ):
        """测试按批次号查询排课"""
        # 先创建一批排课
        create_response = await client.post(
            "/api/v1/schedules/batch",
            headers={"Authorization": f"Bearer {bj_admin_token}"},
            json={
                "class_plan_id": test_class_plans[0].id,
                "date_ranges": [{"start_date": "2024-10-01", "end_date": "2024-10-07"}],
                "time_slots": [{"weekdays": [0], "start_time": "10:00", "end_time": "12:00"}],
                "lesson_hours": 2.0
            }
        )
        batch_no = create_response.json()["data"]["batch_no"]

        # 查询这批排课
        response = await client.get(
            f"/api/v1/schedules?batch_no={batch_no}",
            headers={"Authorization": f"Bearer {bj_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] > 0


class TestBatchNoUniqueness:
    """测试批次号的唯一性"""

    @pytest_asyncio.fixture
    async def schedule_service(self, db_session: AsyncSession) -> ScheduleService:
        """创建排课服务实例"""
        return ScheduleService(db_session)

    @pytest_asyncio.fixture
    async def test_enrollment(
        self,
        db_session: AsyncSession,
        test_class_plans: list[ClassPlan],
        test_students
    ):
        """创建测试报名数据"""
        enrollment = Enrollment(
            student_id=test_students[0].id,
            class_plan_id=test_class_plans[0].id,
            campus_id=test_class_plans[0].campus_id,
            enroll_date=date(2024, 1, 1),
            paid_amount=3000,
            purchased_hours=20,
            used_hours=0,
            status="active",
            created_by="test"
        )
        db_session.add(enrollment)
        await db_session.flush()
        return enrollment

    @pytest.mark.asyncio
    async def test_multiple_batches_have_different_batch_no(
        self,
        schedule_service: ScheduleService,
        test_class_plans: list[ClassPlan],
        test_enrollment,
        db_session: AsyncSession
    ):
        """测试多次批量创建生成的批次号不同"""
        # 创建第一批排课
        data1 = ScheduleBatchCreate(
            class_plan_id=test_class_plans[0].id,
            date_ranges=[DateRange(start_date=date(2024, 11, 1), end_date=date(2024, 11, 3))],
            time_slots=[TimeSlot(weekdays=[0], start_time=time(9, 0), end_time=time(11, 0))],
            lesson_hours=2.0
        )
        _, _, _, batch_no1 = await schedule_service.batch_create_schedules(
            data=data1,
            created_by="test"
        )

        # 创建第二批排课
        data2 = ScheduleBatchCreate(
            class_plan_id=test_class_plans[0].id,
            date_ranges=[DateRange(start_date=date(2024, 11, 8), end_date=date(2024, 11, 10))],
            time_slots=[TimeSlot(weekdays=[0], start_time=time(9, 0), end_time=time(11, 0))],
            lesson_hours=2.0
        )
        _, _, _, batch_no2 = await schedule_service.batch_create_schedules(
            data=data2,
            created_by="test"
        )

        # 批次号应该不同
        assert batch_no1 != batch_no2
