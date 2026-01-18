"""
Authentication service for login, logout, and token management.
"""
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, update, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, UnauthorizedException, ForbiddenException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.models.user import LoginLog, User
from app.models.campus import Campus
from app.models.class_plan import ClassPlan
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.auth import TokenResponse, LoginResponse, CampusOption


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_available_campuses(self, user: User) -> Tuple[bool, List[CampusOption], Optional[int]]:
        """
        Get available campuses for user based on their role.

        Returns:
            Tuple of (need_select_campus, available_campuses, default_campus_id)
        """
        role_code = user.user_role.code if user.user_role else None

        # Student: fixed to one campus
        if role_code == "student":
            # Get student record
            result = await self.db.execute(
                select(Student).where(Student.user_id == user.id)
            )
            student = result.scalar_one_or_none()
            if student and student.campus_id:
                return False, [], student.campus_id
            # Fallback to user's campus_id
            return False, [], user.campus_id

        # Campus admin: fixed to one campus
        if role_code == "campus_admin":
            return False, [], user.campus_id

        # Teacher: show all active campuses for selection
        # 教师可以跨校区上课，登录时直接显示所有校区让他选择
        if role_code == "teacher":
            result = await self.db.execute(
                select(Campus)
                .where(Campus.is_active == True)
                .order_by(Campus.sort_order, Campus.name)
            )
            campuses = result.scalars().all()

            if len(campuses) == 0:
                # No campuses exist, skip selection
                return False, [], None
            elif len(campuses) == 1:
                # Only one campus, auto-select
                return False, [], campuses[0].id
            else:
                # Multiple campuses, need selection
                options = [CampusOption(id=c.id, name=c.name) for c in campuses]
                return True, options, None

        # Super admin: get all active campuses
        if role_code == "super_admin" or (user.role == "admin" and not user.role_id):
            result = await self.db.execute(
                select(Campus)
                .where(Campus.is_active == True)
                .order_by(Campus.name)
            )
            campuses = result.scalars().all()

            if len(campuses) == 0:
                # No campuses, skip selection
                return False, [], None
            elif len(campuses) == 1:
                # Only one campus, auto-select
                return False, [], campuses[0].id
            else:
                # Multiple campuses, need selection
                options = [CampusOption(id=c.id, name=c.name) for c in campuses]
                return True, options, None

        # Default: no campus restriction
        return False, [], None

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """
        Authenticate user and return tokens with campus selection info.

        Args:
            username: User's username
            password: User's password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            LoginResponse with tokens and campus selection info

        Raises:
            UnauthorizedException: If authentication fails
        """
        # Find user with role relation
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_role))
            .where(User.username == username)
        )
        user = result.scalar_one_or_none()

        # Log the attempt
        log = LoginLog(
            user_id=user.id if user else 0,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not user:
            log.status = "failed"
            log.fail_reason = "用户不存在"
            raise UnauthorizedException("用户名或密码错误")

        if not user.is_active:
            log.user_id = user.id
            log.status = "failed"
            log.fail_reason = "用户已被禁用"
            self.db.add(log)
            raise UnauthorizedException("用户已被禁用")

        if not verify_password(password, user.hashed_password):
            log.user_id = user.id
            log.status = "failed"
            log.fail_reason = "密码错误"
            self.db.add(log)
            raise UnauthorizedException("用户名或密码错误")

        # Login successful
        log.user_id = user.id
        log.status = "success"
        self.db.add(log)

        # Update user's online status and last login
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                is_online=True,
                last_login=datetime.now(timezone.utc)
            )
        )

        # Get campus selection info
        need_select, campuses, default_campus_id = await self._get_user_available_campuses(user)

        # Get role code
        role_code = user.user_role.code if user.user_role else None

        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "role_code": role_code,
            "campus_id": default_campus_id  # Will be None if need_select is True
        }

        return LoginResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            need_select_campus=need_select,
            available_campuses=campuses,
            current_campus_id=default_campus_id
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New TokenResponse

        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        payload = verify_token(refresh_token, token_type="refresh")

        if not payload:
            raise UnauthorizedException("无效的刷新令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("无效的刷新令牌")

        # Verify user still exists and is active
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_role))
            .where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("用户不存在或已被禁用")

        # Get role code
        role_code = user.user_role.code if user.user_role else None

        # Preserve campus_id from original token
        campus_id = payload.get("campus_id")

        # Generate new tokens
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "role_code": role_code,
            "campus_id": campus_id  # Preserve campus selection
        }

        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data)
        )

    async def select_campus(self, user: User, campus_id: int) -> LoginResponse:
        """
        Select campus and return new tokens with campus_id.

        Args:
            user: Current authenticated user
            campus_id: Selected campus ID

        Returns:
            LoginResponse with new tokens containing campus_id

        Raises:
            ForbiddenException: If user cannot access the campus
        """
        # Load user role if not loaded
        if not user.user_role:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.user_role))
                .where(User.id == user.id)
            )
            user = result.scalar_one()

        # Verify campus exists and is active
        campus_result = await self.db.execute(
            select(Campus).where(Campus.id == campus_id, Campus.is_active == True)
        )
        campus = campus_result.scalar_one_or_none()

        if not campus:
            raise BadRequestException("校区不存在或已禁用")

        # Get available campuses for validation
        _, available_campuses, _ = await self._get_user_available_campuses(user)

        role_code = user.user_role.code if user.user_role else None

        # Validate user can access this campus
        if role_code == "super_admin" or (user.role == "admin" and not user.role_id):
            # Super admin can access any campus
            pass
        elif role_code == "teacher":
            # Teacher can access any active campus (they may teach across campuses)
            pass
        else:
            # Campus admin / student - should not reach here as they have fixed campus
            raise ForbiddenException("您没有该校区的访问权限")

        # Generate new tokens with campus_id
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "role_code": role_code,
            "campus_id": campus_id
        }

        return LoginResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            need_select_campus=False,
            available_campuses=[],
            current_campus_id=campus_id
        )

    async def logout(self, user: User) -> None:
        """
        Logout user and mark as offline.

        Args:
            user: Current user
        """
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(is_online=False)
        )

    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str
    ) -> None:
        """
        Change user's password.

        Args:
            user: Current user
            old_password: Current password
            new_password: New password

        Raises:
            BadRequestException: If old password is incorrect
        """
        if not verify_password(old_password, user.hashed_password):
            raise BadRequestException("原密码错误")

        hashed = get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(hashed_password=hashed)
        )

    async def update_profile(
        self,
        user: User,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> User:
        """
        Update current user's profile.

        Args:
            user: Current user
            email: New email (optional)
            phone: New phone (optional)
            avatar: New avatar URL (optional)

        Returns:
            Updated user instance
        """
        from app.core.exceptions import ConflictException

        update_dict = {}

        if email is not None and email != user.email:
            # Check for existing email
            result = await self.db.execute(
                select(User).where(User.email == email, User.id != user.id)
            )
            if result.scalar_one_or_none():
                raise ConflictException(f"邮箱 '{email}' 已被使用")
            update_dict["email"] = email

        if phone is not None and phone != user.phone:
            # Check for existing phone
            result = await self.db.execute(
                select(User).where(User.phone == phone, User.id != user.id)
            )
            if result.scalar_one_or_none():
                raise ConflictException(f"手机号 '{phone}' 已被使用")
            update_dict["phone"] = phone

        if avatar is not None:
            update_dict["avatar"] = avatar

        if update_dict:
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(**update_dict)
            )
            await self.db.refresh(user)

        return user
