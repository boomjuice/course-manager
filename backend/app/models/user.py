"""
User related models: User, Role, LoginLog.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.teacher import Teacher
    from app.models.student import Student
    from app.models.permission import UserRole
    from app.models.campus import Campus


class Role(str, Enum):
    """User roles enumeration. (兼容旧版，新版使用role_id关联UserRole表)"""
    ADMIN = "admin"      # Administrator: full access
    TEACHER = "teacher"  # Teacher: view own courses
    STUDENT = "student"  # Student: view own courses


class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="用户名"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
        comment="邮箱"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
        comment="手机号"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希"
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=Role.STUDENT.value,
        comment="角色(兼容旧版)"
    )
    # 新增: RBAC角色关联
    role_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="角色ID（关联roles表）"
    )
    # 新增: 校区关联（校区管理员必填）
    campus_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属校区ID（校区管理员必填）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )
    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否在线"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间"
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="头像URL"
    )

    # Relationships
    login_logs: Mapped[List["LoginLog"]] = relationship(
        "LoginLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    # RBAC角色关联
    user_role: Mapped[Optional["UserRole"]] = relationship(
        "UserRole",
        foreign_keys=[role_id]
    )
    # 校区关联
    campus: Mapped[Optional["Campus"]] = relationship(
        "Campus",
        foreign_keys=[campus_id]
    )
    # teacher: Mapped[Optional["Teacher"]] = relationship(back_populates="user")
    # student: Mapped[Optional["Student"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class LoginLog(BaseModel):
    """
    Login log model for tracking user login attempts.
    """
    __tablename__ = "login_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    login_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="登录时间"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="浏览器UA"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
        comment="登录状态：success/failed"
    )
    fail_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="失败原因"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="login_logs")

    def __repr__(self) -> str:
        return f"<LoginLog(id={self.id}, user_id={self.user_id}, status={self.status})>"
