"""
LessonRecord model - 课时消耗记录
记录每次排课消耗的课时明细
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Integer, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LessonRecord(BaseModel):
    """
    课时消耗记录 - 记录每次排课完成后消耗的课时
    """
    __tablename__ = "lesson_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="报名记录ID"
    )
    schedule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="排课ID"
    )
    record_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="消耗日期"
    )
    hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 1),
        nullable=False,
        comment="消耗课时数"
    )
    type: Mapped[str] = mapped_column(
        String(20),
        default="schedule",
        nullable=False,
        comment="类型: schedule(排课消耗)/manual(手动调整)/refund(退费扣减)"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )

    # Relationships
    enrollment = relationship("Enrollment", backref="lesson_records")
    schedule = relationship("Schedule", backref="lesson_records")

    def __repr__(self) -> str:
        return f"<LessonRecord(id={self.id}, enrollment_id={self.enrollment_id}, hours={self.hours})>"
