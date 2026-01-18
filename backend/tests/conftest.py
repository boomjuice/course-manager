"""
Pytest configuration and fixtures for testing.
测试配置和公共fixture。
"""
import asyncio
from datetime import date, time
from decimal import Decimal
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import ARRAY

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.campus import Campus, Classroom
from app.models.permission import Resource, Permission, UserRole, RolePermission
from app.models.student import Student
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.class_plan import ClassPlan
from app.models.schedule import Schedule
from app.models.enrollment import Enrollment
from app.core.security import get_password_hash, create_access_token


# 使用内存SQLite进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# SQLite不支持ARRAY类型，用JSON替代
# 直接替换Student和Teacher模型中的ARRAY列类型
def _patch_array_columns():
    """
    在测试时将ARRAY列类型替换为JSON以兼容SQLite。
    这是个hack，生产环境仍使用PostgreSQL的ARRAY类型。
    """
    from app.models.student import Student
    from app.models.teacher import Teacher

    # Patch Student model ARRAY columns
    if hasattr(Student, '__table__'):
        for col in Student.__table__.columns:
            if isinstance(col.type, ARRAY):
                col.type = JSON()

    # Patch Teacher model ARRAY columns
    if hasattr(Teacher, '__table__'):
        for col in Teacher.__table__.columns:
            if isinstance(col.type, ARRAY):
                col.type = JSON()


# 在导入时执行patch
_patch_array_columns()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden dependencies."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ========== 数据 Fixtures ==========

@pytest_asyncio.fixture
async def test_campuses(db_session: AsyncSession) -> list[Campus]:
    """Create test campuses."""
    campus1 = Campus(
        name="北京校区",
        address="北京市朝阳区",
        is_active=True,
        created_by="test",
    )
    campus2 = Campus(
        name="上海校区",
        address="上海市浦东新区",
        is_active=True,
        created_by="test",
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()
    return [campus1, campus2]


@pytest_asyncio.fixture
async def test_classrooms(db_session: AsyncSession, test_campuses: list[Campus]) -> list[Classroom]:
    """Create test classrooms."""
    classroom1 = Classroom(
        name="101教室",
        campus_id=test_campuses[0].id,
        capacity=30,
        is_active=True,
        created_by="test",
    )
    classroom2 = Classroom(
        name="201教室",
        campus_id=test_campuses[1].id,
        capacity=25,
        is_active=True,
        created_by="test",
    )
    db_session.add_all([classroom1, classroom2])
    await db_session.flush()
    return [classroom1, classroom2]


@pytest_asyncio.fixture
async def test_resources(db_session: AsyncSession) -> list[Resource]:
    """Create test resources (permission modules)."""
    resources_data = [
        ("dashboard", "仪表盘"),
        ("student", "学生管理"),
        ("teacher", "教师管理"),
        ("course", "课程管理"),
        ("class_plan", "开班管理"),
        ("enrollment", "报名管理"),
        ("schedule", "排课管理"),
        ("campus", "校区管理"),
        ("user", "用户管理"),
        ("role_permission", "角色权限"),
    ]
    resources = []
    for i, (code, name) in enumerate(resources_data):
        resource = Resource(
            code=code,
            name=name,
            sort_order=i,
            is_active=True,
            created_by="test",
        )
        resources.append(resource)

    db_session.add_all(resources)
    await db_session.flush()
    return resources


@pytest_asyncio.fixture
async def test_permissions(db_session: AsyncSession, test_resources: list[Resource]) -> list[Permission]:
    """Create test permissions for each resource."""
    permissions = []
    for resource in test_resources:
        for action in ["read", "edit", "delete"]:
            perm = Permission(
                resource_id=resource.id,
                action=action,
                name=f"{resource.name}-{action}",
                created_by="test",
            )
            permissions.append(perm)

    db_session.add_all(permissions)
    await db_session.flush()
    return permissions


@pytest_asyncio.fixture
async def test_roles(db_session: AsyncSession, test_permissions: list[Permission]) -> dict[str, UserRole]:
    """Create test roles with permissions."""
    # 创建角色
    super_admin = UserRole(
        code="super_admin",
        name="超级管理员",
        is_system=True,
        is_active=True,
        created_by="test",
    )
    campus_admin = UserRole(
        code="campus_admin",
        name="校区管理员",
        is_system=True,
        is_active=True,
        created_by="test",
    )
    teacher_role = UserRole(
        code="teacher",
        name="教师",
        is_system=True,
        is_active=True,
        created_by="test",
    )
    student_role = UserRole(
        code="student",
        name="学生",
        is_system=True,
        is_active=True,
        created_by="test",
    )

    db_session.add_all([super_admin, campus_admin, teacher_role, student_role])
    await db_session.flush()

    # 为角色分配权限
    # super_admin: 所有权限
    for perm in test_permissions:
        db_session.add(RolePermission(role_id=super_admin.id, permission_id=perm.id))

    # campus_admin: 通过permission.name判断，包含学生/课程/开班/报名/排课的权限
    campus_keywords = ["学生", "课程", "开班", "报名", "排课", "仪表盘", "教师"]
    campus_perm_ids = [p.id for p in test_permissions if any(kw in p.name for kw in campus_keywords)]
    for perm_id in campus_perm_ids:
        db_session.add(RolePermission(role_id=campus_admin.id, permission_id=perm_id))

    # teacher: 只有read权限（前5个）
    teacher_perm_ids = [p.id for p in test_permissions if "-read" in p.name]
    for perm_id in teacher_perm_ids[:5]:
        db_session.add(RolePermission(role_id=teacher_role.id, permission_id=perm_id))

    # student: 最少权限，只有排课的read权限
    student_perm_ids = [p.id for p in test_permissions if ("排课" in p.name or "仪表盘" in p.name) and "-read" in p.name]
    for perm_id in student_perm_ids:
        db_session.add(RolePermission(role_id=student_role.id, permission_id=perm_id))

    await db_session.flush()

    return {
        "super_admin": super_admin,
        "campus_admin": campus_admin,
        "teacher": teacher_role,
        "student": student_role,
    }


@pytest_asyncio.fixture
async def test_users(
    db_session: AsyncSession,
    test_campuses: list[Campus],
    test_roles: dict[str, UserRole]
) -> dict[str, User]:
    """Create test users with different roles."""
    # 超级管理员（无校区限制）
    super_admin = User(
        username="admin",
        phone="13800000001",
        hashed_password=get_password_hash("123456"),
        role="admin",
        role_id=test_roles["super_admin"].id,
        campus_id=None,  # 超管无校区限制
        is_active=True,
        created_by="test",
        updated_by="test",
    )

    # 北京校区管理员
    bj_campus_admin = User(
        username="bj_admin",
        phone="13800000002",
        hashed_password=get_password_hash("123456"),
        role="admin",
        role_id=test_roles["campus_admin"].id,
        campus_id=test_campuses[0].id,  # 北京校区
        is_active=True,
        created_by="test",
        updated_by="test",
    )

    # 上海校区管理员
    sh_campus_admin = User(
        username="sh_admin",
        phone="13800000003",
        hashed_password=get_password_hash("123456"),
        role="admin",
        role_id=test_roles["campus_admin"].id,
        campus_id=test_campuses[1].id,  # 上海校区
        is_active=True,
        created_by="test",
        updated_by="test",
    )

    # 教师
    teacher_user = User(
        username="teacher1",
        phone="13800000004",
        hashed_password=get_password_hash("123456"),
        role="teacher",
        role_id=test_roles["teacher"].id,
        campus_id=test_campuses[0].id,
        is_active=True,
        created_by="test",
        updated_by="test",
    )

    # 学生
    student_user = User(
        username="student1",
        phone="13800000005",
        hashed_password=get_password_hash("123456"),
        role="student",
        role_id=test_roles["student"].id,
        campus_id=test_campuses[0].id,
        is_active=True,
        created_by="test",
        updated_by="test",
    )

    db_session.add_all([super_admin, bj_campus_admin, sh_campus_admin, teacher_user, student_user])
    await db_session.flush()

    return {
        "super_admin": super_admin,
        "bj_campus_admin": bj_campus_admin,
        "sh_campus_admin": sh_campus_admin,
        "teacher": teacher_user,
        "student": student_user,
    }


@pytest_asyncio.fixture
async def test_teachers(db_session: AsyncSession) -> list[Teacher]:
    """Create test teachers (no campus restriction)."""
    teacher1 = Teacher(
        name="张老师",
        phone="13900000001",
        subjects=["数学", "物理"],
        is_active=True,
        created_by="test",
    )
    teacher2 = Teacher(
        name="李老师",
        phone="13900000002",
        subjects=["英语"],
        is_active=True,
        created_by="test",
    )
    db_session.add_all([teacher1, teacher2])
    await db_session.flush()
    return [teacher1, teacher2]


@pytest_asyncio.fixture
async def test_courses(db_session: AsyncSession, test_campuses: list[Campus]) -> list[Course]:
    """Create test courses with campus isolation."""
    # 北京校区的课程
    course_bj = Course(
        name="高中数学",
        code="MATH-BJ-001",
        campus_id=test_campuses[0].id,
        subject="数学",
        unit_price=Decimal("150.00"),
        is_active=True,
        created_by="test",
    )
    # 上海校区的课程
    course_sh = Course(
        name="高中英语",
        code="ENG-SH-001",
        campus_id=test_campuses[1].id,
        subject="英语",
        unit_price=Decimal("125.00"),
        is_active=True,
        created_by="test",
    )
    db_session.add_all([course_bj, course_sh])
    await db_session.flush()
    return [course_bj, course_sh]


@pytest_asyncio.fixture
async def test_students(db_session: AsyncSession, test_campuses: list[Campus]) -> list[Student]:
    """Create test students with campus isolation."""
    # 北京校区的学生
    student_bj = Student(
        name="小明",
        phone="13600000001",
        campus_id=test_campuses[0].id,
        status="active",
        is_active=True,
        created_by="test",
    )
    # 上海校区的学生
    student_sh = Student(
        name="小红",
        phone="13600000002",
        campus_id=test_campuses[1].id,
        status="active",
        is_active=True,
        created_by="test",
    )
    db_session.add_all([student_bj, student_sh])
    await db_session.flush()
    return [student_bj, student_sh]


@pytest_asyncio.fixture
async def test_class_plans(
    db_session: AsyncSession,
    test_campuses: list[Campus],
    test_courses: list[Course],
    test_teachers: list[Teacher],
    test_classrooms: list[Classroom],
) -> list[ClassPlan]:
    """Create test class plans with campus isolation."""
    # 北京校区的班级
    plan_bj = ClassPlan(
        name="高中数学精品班",
        course_id=test_courses[0].id,
        campus_id=test_campuses[0].id,
        teacher_id=test_teachers[0].id,
        classroom_id=test_classrooms[0].id,
        max_students=20,
        status="ongoing",
        is_active=True,
        created_by="test",
    )
    # 上海校区的班级
    plan_sh = ClassPlan(
        name="高中英语冲刺班",
        course_id=test_courses[1].id,
        campus_id=test_campuses[1].id,
        teacher_id=test_teachers[1].id,
        classroom_id=test_classrooms[1].id,
        max_students=15,
        status="ongoing",
        is_active=True,
        created_by="test",
    )
    db_session.add_all([plan_bj, plan_sh])
    await db_session.flush()
    return [plan_bj, plan_sh]


# ========== Token Fixtures ==========

def create_test_token(user: User, campus_id: int = None) -> str:
    """
    Create JWT token for test user with campus_id and role_code.
    新架构下JWT必须包含campus_id用于数据过滤。
    """
    role_code = None
    if hasattr(user, 'user_role') and user.user_role:
        role_code = user.user_role.code
    elif hasattr(user, 'role_id') and user.role_id:
        # 如果已经加载了role_id但没有加载关系，根据常见模式推断
        pass  # 这种情况在测试中不太常见

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "role_code": role_code,
        "campus_id": campus_id if campus_id else user.campus_id,
    }
    return create_access_token(data=token_data)


@pytest.fixture
def super_admin_token(test_users: dict[str, User], test_campuses: list[Campus]) -> str:
    """
    Get token for super admin.
    超管默认选择第一个校区，这样才能通过校区过滤获取数据。
    """
    user = test_users["super_admin"]
    # 超管在测试中默认选择第一个校区
    return create_access_token(data={
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "role_code": "super_admin",
        "campus_id": test_campuses[0].id,  # 默认选择北京校区
    })


@pytest.fixture
def bj_admin_token(test_users: dict[str, User], test_campuses: list[Campus]) -> str:
    """Get token for Beijing campus admin."""
    user = test_users["bj_campus_admin"]
    return create_access_token(data={
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "role_code": "campus_admin",
        "campus_id": test_campuses[0].id,  # 北京校区
    })


@pytest.fixture
def sh_admin_token(test_users: dict[str, User], test_campuses: list[Campus]) -> str:
    """Get token for Shanghai campus admin."""
    user = test_users["sh_campus_admin"]
    return create_access_token(data={
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "role_code": "campus_admin",
        "campus_id": test_campuses[1].id,  # 上海校区
    })


@pytest.fixture
def teacher_token(test_users: dict[str, User], test_campuses: list[Campus]) -> str:
    """Get token for teacher."""
    user = test_users["teacher"]
    return create_access_token(data={
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "role_code": "teacher",
        "campus_id": test_campuses[0].id,  # 北京校区
    })


@pytest.fixture
def student_token(test_users: dict[str, User], test_campuses: list[Campus]) -> str:
    """Get token for student."""
    user = test_users["student"]
    return create_access_token(data={
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "role_code": "student",
        "campus_id": test_campuses[0].id,  # 北京校区
    })
