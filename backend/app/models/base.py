"""
Base model with common fields for all models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BaseModel(Base):
    """
    Abstract base model with common audit fields.
    All models should inherit from this class.
    """
    __abstract__ = True

    created_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        comment="更新时间"
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="创建人"
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="最后修改人"
    )
