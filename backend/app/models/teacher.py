"""
Teacher model.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Date, Integer, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Teacher(BaseModel):
    """
    Teacher model.
    """
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Optional link to user account for teacher login
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        comment="关联用户账号ID"
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="教师姓名"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="性别"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="联系电话"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="电子邮箱"
    )
    id_card: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="身份证号"
    )
    entry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="入职日期"
    )
    education: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="学历（字典值: education）"
    )
    major: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="专业"
    )
    # 教师负责的科目（多选，存储字典值数组）
    subjects: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        comment="负责科目（字典值数组: subject）"
    )
    # 教师负责的年级（多选，存储字典值数组）
    grade_levels: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(20)),
        nullable=True,
        comment="负责年级（字典值数组: grade）"
    )
    hourly_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="课时费单价"
    )
    introduction: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="简介"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
        comment="状态（字典值: teacher_status）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, name={self.name})>"
