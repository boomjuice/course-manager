"""
Data dictionary models for system configuration.
"""
from typing import Optional, List

from sqlalchemy import Boolean, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DictType(BaseModel):
    """
    Dictionary type model - categories of dictionary items.
    Examples: course_level, student_status, payment_method, etc.
    """
    __tablename__ = "dict_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="字典类型编码"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="字典类型名称"
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
        comment="是否系统内置（系统内置不可删除）"
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
    items: Mapped[List["DictItem"]] = relationship(
        "DictItem",
        back_populates="dict_type",
        cascade="all, delete-orphan",
        order_by="DictItem.sort_order"
    )

    def __repr__(self) -> str:
        return f"<DictType(id={self.id}, code={self.code}, name={self.name})>"


class DictItem(BaseModel):
    """
    Dictionary item model - actual values for each dictionary type.
    """
    __tablename__ = "dict_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dict_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="字典类型ID"
    )
    value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="字典值"
    )
    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="显示标签"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="显示颜色（用于标签等）"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否默认值"
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
    dict_type: Mapped["DictType"] = relationship("DictType", back_populates="items")

    def __repr__(self) -> str:
        return f"<DictItem(id={self.id}, value={self.value}, label={self.label})>"
