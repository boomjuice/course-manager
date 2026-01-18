"""
Enrollment model - student enrollment records.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Integer, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Enrollment(BaseModel):
    """
    Enrollment model - represents a student's enrollment in a class plan.
    添加campus_id冗余字段避免JOIN查询。
    """
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="学生ID"
    )
    class_plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("class_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="班级计划ID"
    )
    # 校区归属（冗余字段，避免JOIN查询）
    campus_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属校区ID（从ClassPlan自动获取）"
    )
    enroll_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="报名日期"
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="付款金额"
    )
    purchased_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 1),
        default=Decimal("0.0"),
        nullable=False,
        comment="购买课时"
    )
    used_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 1),
        default=Decimal("0.0"),
        nullable=False,
        comment="已使用课时"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
        comment="状态: active/completed/refunded/cancelled"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )

    # Relationships
    student = relationship("Student", backref="enrollments")
    class_plan = relationship("ClassPlan", backref="enrollments")
    campus = relationship("Campus", foreign_keys=[campus_id])

    def __repr__(self) -> str:
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, class_plan_id={self.class_plan_id})>"
