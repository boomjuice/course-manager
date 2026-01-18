"""
Common Pydantic schemas for API responses.
"""
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with total count and items."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    page_size: int
    items: List[T]


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class ErrorResponse(BaseModel):
    """Error response format."""

    code: int
    message: str
    detail: Optional[Any] = None


# ========== 统一响应辅助函数 ==========

def success_response(data: Any = None, message: str = "success", total: int = None, page: int = None, page_size: int = None) -> ResponseModel:
    """
    统一成功响应格式。
    - data: dict 类型 (如 {"items": [...], "total": 100})
    - data 是 list 时，会自动放入 data.items
    - total: 分页总数（兼容旧接口）
    - page: 当前页码
    - page_size: 每页数量

    Args:
        data: 响应数据
        message: 响应消息
        total: 分页总数
        page: 当前页码
        page_size: 每页数量

    Returns:
        ResponseModel 对象
    """
    # 如果 data 是 list，自动放入 data.items，total 也放入 data
    if isinstance(data, list):
        return ResponseModel(
            code=0,
            message=message,
            data={"items": data, "total": total, "page": page, "page_size": page_size},
        )
    return ResponseModel(
        code=0,
        message=message,
        data=data,
    )


def error_response(code: int, message: str, detail: Any = None) -> ResponseModel:
    """
    统一错误响应格式。

    Args:
        code: 错误码
        message: 错误消息
        detail: 详细信息

    Returns:
        ResponseModel 对象
    """
    return ResponseModel(
        code=code,
        message=message,
        data=None,
    )
