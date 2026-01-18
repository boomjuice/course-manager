"""
User management service for CRUD operations.
支持RBAC角色和校区关联。
"""
from typing import List, Optional

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.security import get_password_hash
from app.models.user import LoginLog, Role, User
from app.models.permission import UserRole
from app.models.campus import Campus
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for handling user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate, created_by: str) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data
            created_by: Username of creator

        Returns:
            Created user instance

        Raises:
            ConflictException: If username/email/phone already exists
        """
        # Check for existing username
        existing = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"用户名 '{user_data.username}' 已存在")

        # Check for existing email if provided
        if user_data.email:
            existing = await self.db.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"邮箱 '{user_data.email}' 已被使用")

        # Check for existing phone if provided
        if user_data.phone:
            existing = await self.db.execute(
                select(User).where(User.phone == user_data.phone)
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"手机号 '{user_data.phone}' 已被使用")

        # Create user with RBAC support
        user = User(
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role.value,
            role_id=user_data.role_id,  # RBAC角色ID
            campus_id=user_data.campus_id,  # 所属校区
            is_active=user_data.is_active,
            avatar=user_data.avatar,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(user)
        await self.db.flush()

        # 重新查询以加载关系
        return await self.get_user_by_id(user.id)

    async def get_user_by_id(self, user_id: int) -> User:
        """
        Get user by ID with role and campus relationships.

        Args:
            user_id: User ID

        Returns:
            User instance with relationships loaded

        Raises:
            NotFoundException: If user not found
        """
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.user_role),  # 加载RBAC角色
                selectinload(User.campus),  # 加载校区
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"用户ID {user_id} 不存在")

        return user

    async def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_online: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[List[User], int]:
        """
        Get paginated list of users with filters.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            role: Filter by role (legacy)
            role_id: Filter by RBAC role ID
            is_active: Filter by active status
            is_online: Filter by online status
            search: Search by username/email/phone

        Returns:
            Tuple of (users list, total count)
        """
        query = select(User).options(
            selectinload(User.user_role),  # 预加载RBAC角色
            selectinload(User.campus),  # 预加载校区
        )

        # Apply filters
        if role:
            query = query.where(User.role == role)
        if role_id:
            query = query.where(User.role_id == role_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if is_online is not None:
            query = query.where(User.is_online == is_online)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.username.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)) |
                (User.phone.ilike(search_pattern))
            )

        # Get total count (without options for efficiency)
        count_subquery = select(User.id)
        if role:
            count_subquery = count_subquery.where(User.role == role)
        if role_id:
            count_subquery = count_subquery.where(User.role_id == role_id)
        if is_active is not None:
            count_subquery = count_subquery.where(User.is_active == is_active)
        if is_online is not None:
            count_subquery = count_subquery.where(User.is_online == is_online)
        if search:
            search_pattern = f"%{search}%"
            count_subquery = count_subquery.where(
                (User.username.ilike(search_pattern)) |
                (User.email.ilike(search_pattern)) |
                (User.phone.ilike(search_pattern))
            )
        count_query = select(func.count()).select_from(count_subquery.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(User.created_time.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by: str
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID to update
            user_data: Update data
            updated_by: Username of updater

        Returns:
            Updated user instance

        Raises:
            NotFoundException: If user not found
            ConflictException: If username/email/phone conflicts
        """
        user = await self.get_user_by_id(user_id)

        update_dict = user_data.model_dump(exclude_unset=True)

        # Check for conflicts
        if "username" in update_dict and update_dict["username"] != user.username:
            existing = await self.db.execute(
                select(User).where(User.username == update_dict["username"])
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"用户名 '{update_dict['username']}' 已存在")

        if "email" in update_dict and update_dict["email"] != user.email:
            existing = await self.db.execute(
                select(User).where(User.email == update_dict["email"])
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"邮箱 '{update_dict['email']}' 已被使用")

        if "phone" in update_dict and update_dict["phone"] != user.phone:
            existing = await self.db.execute(
                select(User).where(User.phone == update_dict["phone"])
            )
            if existing.scalar_one_or_none():
                raise ConflictException(f"手机号 '{update_dict['phone']}' 已被使用")

        # Convert role enum to string if present
        if "role" in update_dict and update_dict["role"]:
            update_dict["role"] = update_dict["role"].value

        update_dict["updated_by"] = updated_by

        await self.db.execute(
            update(User).where(User.id == user_id).values(**update_dict)
        )
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        """
        Delete a user (hard delete).

        Args:
            user_id: User ID to delete

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        await self.db.delete(user)

    async def reset_password(
        self,
        user_id: int,
        new_password: str,
        updated_by: str
    ) -> None:
        """
        Reset user's password (admin operation).

        Args:
            user_id: User ID
            new_password: New password
            updated_by: Admin username
        """
        await self.get_user_by_id(user_id)

        hashed = get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hashed, updated_by=updated_by)
        )

    async def get_login_logs(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[LoginLog], int]:
        """
        Get user's login logs.

        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (logs list, total count)
        """
        # Verify user exists
        await self.get_user_by_id(user_id)

        query = select(LoginLog).where(LoginLog.user_id == user_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(LoginLog.login_time.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def get_online_users(self) -> List[User]:
        """
        Get all online users.

        Returns:
            List of online users
        """
        result = await self.db.execute(
            select(User).where(User.is_online == True).order_by(User.last_login.desc())
        )
        return list(result.scalars().all())

    async def get_all_login_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[LoginLog], int]:
        """
        Get all login logs with filters (admin view).

        Args:
            page: Page number
            page_size: Items per page
            user_id: Filter by user ID
            status: Filter by status (success/failed)
            search: Search by username/IP

        Returns:
            Tuple of (logs list, total count)
        """
        from sqlalchemy.orm import selectinload

        query = select(LoginLog).options(selectinload(LoginLog.user))

        # Apply filters
        if user_id:
            query = query.where(LoginLog.user_id == user_id)
        if status:
            query = query.where(LoginLog.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.join(User).where(
                (User.username.ilike(search_pattern)) |
                (LoginLog.ip_address.ilike(search_pattern))
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(LoginLog.login_time.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total
