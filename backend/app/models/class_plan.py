"""
Class plan model - scheduled course offerings.
"""
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ClassPlan(BaseModel):
    """
    Class plan model - represents a scheduled course offering.
    A course product can have multiple class plans (different sessions/terms).
    """
    __tablename__ = "class_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="班级名称"
    )
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="课程产品ID"
    )
    teacher_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="主讲教师ID"
    )
    campus_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="上课校区ID"
    )
    classroom_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("classrooms.id", ondelete="SET NULL"),
        nullable=True,
        comment="默认教室ID"
    )
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="开班日期"
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="结束日期"
    )
    max_students: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False,
        comment="最大人数"
    )
    current_students: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前人数"
    )
    total_lessons: Mapped[float] = mapped_column(
        Numeric(6, 1),
        default=0.0,
        nullable=False,
        comment="总课次（支持小数课时）"
    )
    completed_lessons: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="已完成课次"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="状态：pending/ongoing/completed/cancelled"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # Relationships
    course = relationship("Course", foreign_keys=[course_id])
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
    campus = relationship("Campus", foreign_keys=[campus_id])
    classroom = relationship("Classroom", foreign_keys=[classroom_id])

    def __repr__(self) -> str:
        return f"<ClassPlan(id={self.id}, name={self.name})>"
