"""
Course product models.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Course(BaseModel):
    """
    Course product model - templates for course offerings.
    每个课程产品归属于一个校区，各校区有独立的课程产品库。
    """
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 校区归属（SaaS隔离）
    campus_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属校区ID"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="课程名称"
    )
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="课程编码"
    )
    # 学科（单选）
    subject: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="学科（字典值: subject）"
    )
    # 年级（单选）
    grade_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="年级（字典值: grade）"
    )
    level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="难度级别（字典值: course_level）"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="课时单价（开班时可修改）"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="课程描述"
    )
    objectives: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="学习目标"
    )
    target_audience: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="适合人群"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序"
    )

    # Relationships
    campus = relationship("Campus", foreign_keys=[campus_id])

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name={self.name}, code={self.code})>"
