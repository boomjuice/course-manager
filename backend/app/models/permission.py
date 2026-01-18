"""
RBAC Permission models: Resource, Permission, UserRole, RolePermission.
权限系统核心模型，支持可配置的角色权限管理。
"""
from typing import List, Optional

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Resource(BaseModel):
    """
    系统资源模块表。
    定义系统中的各个功能模块，如：学生管理、课程管理、校区管理等。
    """
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="资源编码 (dashboard/student/teacher/course等)"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="资源名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # Relationships
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        back_populates="resource",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, code={self.code}, name={self.name})>"


class Permission(BaseModel):
    """
    权限定义表。
    每个权限是资源+操作的组合，如：student:read, student:edit, student:delete
    """
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('resource_id', 'action', name='uq_permission_resource_action'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="资源ID"
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="操作类型: read/edit/delete"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="权限名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )

    # Relationships
    resource: Mapped["Resource"] = relationship("Resource", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, resource_id={self.resource_id}, action={self.action})>"


class UserRole(BaseModel):
    """
    角色定义表。
    系统内置角色: super_admin, campus_admin, teacher, student
    支持自定义角色扩展。
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="角色编码 (super_admin/campus_admin/teacher/student)"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="角色名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否系统内置角色（不可删除）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserRole(id={self.id}, code={self.code}, name={self.name})>"


class RolePermission(BaseModel):
    """
    角色-权限关联表。
    定义每个角色拥有哪些权限。
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="角色ID"
    )
    permission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="权限ID"
    )

    # Relationships
    role: Mapped["UserRole"] = relationship("UserRole", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission")

    def __repr__(self) -> str:
        return f"<RolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"
