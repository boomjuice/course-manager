"""
Campus and Classroom models.
"""
from typing import Optional, List, Dict

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Campus(BaseModel):
    """
    Campus model - training locations.
    """
    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="校区名称"
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="详细地址"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="联系电话"
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="联系人"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
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
    classrooms: Mapped[List["Classroom"]] = relationship(
        "Classroom",
        back_populates="campus",
        cascade="all, delete-orphan",
        order_by="Classroom.sort_order"
    )

    def __repr__(self) -> str:
        return f"<Campus(id={self.id}, name={self.name})>"


class Classroom(BaseModel):
    """
    Classroom model - rooms within a campus.
    """
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campus_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campuses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属校区ID"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="教室名称"
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False,
        comment="容纳人数"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )
    equipment: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="设备配置（key-value形式）"
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
    campus: Mapped["Campus"] = relationship("Campus", back_populates="classrooms")

    def __repr__(self) -> str:
        return f"<Classroom(id={self.id}, name={self.name}, campus_id={self.campus_id})>"
