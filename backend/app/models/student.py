"""
Student model.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Date, Integer, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Student(BaseModel):
    """
    Student model - the core business entity.
    每个学生归属于一个校区，校区管理员只能管理自己校区的学生。
    """
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Optional link to user account for student login
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        comment="关联用户账号ID"
    )
    # 校区归属（SaaS隔离）
    campus_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属校区ID"
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="学生姓名"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="性别"
    )
    birthday: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="生日"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="联系电话"
    )
    parent_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="家长姓名"
    )
    parent_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="家长电话"
    )
    school: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="就读学校"
    )
    grade: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="年级（字典值: grade）"
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="家庭住址"
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="来源渠道（字典值: student_source）"
    )
    # 学生标签系统
    subject_levels: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="科目水平标签（格式: subject:level，如 math:excellent）"
    )
    learning_goals: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        comment="学习目标（字典值数组: learning_goal）"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )
    # Balance tracking
    total_hours: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="总购买课时"
    )
    remaining_hours: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="剩余课时"
    )
    total_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="累计付款"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
        comment="状态（字典值: student_status）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    campus = relationship("Campus", foreign_keys=[campus_id])

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, name={self.name})>"
