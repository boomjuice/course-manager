"""
Schedule model - individual class session records.
"""
from datetime import date, time
from typing import Optional

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Schedule(BaseModel):
    """
    Schedule model - represents a single class session.
    Each class plan can have multiple schedules (individual lessons).
    添加campus_id冗余字段避免JOIN查询，添加batch_no支持批量排课操作。
    """
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("class_plans.id", ondelete="CASCADE"),
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
    # 排课批次号（支持批量操作）
    batch_no: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="排课批次号（批量排课时生成）"
    )
    teacher_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="授课教师ID (可覆盖班级默认)"
    )
    classroom_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("classrooms.id", ondelete="SET NULL"),
        nullable=True,
        comment="教室ID (可覆盖班级默认)"
    )
    schedule_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="上课日期"
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="开始时间"
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="结束时间"
    )
    lesson_hours: Mapped[float] = mapped_column(
        Numeric(6, 1),
        default=2.0,
        nullable=False,
        comment="课时数（支持小数，如1.5课时）"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="课程标题/内容"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",
        nullable=False,
        index=True,
        comment="状态: scheduled/completed/cancelled"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )

    # Relationships
    class_plan = relationship("ClassPlan", backref="schedules")
    campus = relationship("Campus", foreign_keys=[campus_id])
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
    classroom = relationship("Classroom", foreign_keys=[classroom_id])

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, date={self.schedule_date})>"
