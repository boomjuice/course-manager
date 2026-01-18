"""
StudentAttendance model - 学生出勤记录
记录学生在每次排课的出勤状态（正常、请假、缺勤）
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class StudentAttendance(BaseModel):
    """
    学生出勤记录 - 记录学生在每次排课的出勤状态
    """
    __tablename__ = "student_attendances"

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
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="排课ID"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
        index=True,
        comment="出勤状态: normal(正常)/leave(请假)/absent(缺勤)"
    )
    leave_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="请假原因（仅请假时填写）"
    )
    apply_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="请假申请时间"
    )
    deduct_hours: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否扣课时（请假通常不扣，缺勤可扣）"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )

    # Relationships
    enrollment = relationship("Enrollment", backref="attendances")
    schedule = relationship("Schedule", backref="student_attendances")

    def __repr__(self) -> str:
        return f"<StudentAttendance(id={self.id}, enrollment_id={self.enrollment_id}, status={self.status})>"
