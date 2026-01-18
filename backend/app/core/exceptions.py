"""
Custom exceptions for the application.
"""
from typing import Any, Optional


class CourseManagerException(Exception):
    """Base exception for course manager application."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        detail: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class UnauthorizedException(CourseManagerException):
    """Exception for unauthorized access (401)."""

    def __init__(self, message: str = "认证失败", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=401, detail=detail)


class ForbiddenException(CourseManagerException):
    """Exception for forbidden access (403)."""

    def __init__(self, message: str = "权限不足", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=403, detail=detail)


class NotFoundException(CourseManagerException):
    """Exception for resource not found (404)."""

    def __init__(self, message: str = "资源不存在", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=404, detail=detail)


class BadRequestException(CourseManagerException):
    """Exception for bad request (400)."""

    def __init__(self, message: str = "请求参数错误", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=400, detail=detail)


class ConflictException(CourseManagerException):
    """Exception for resource conflict (409)."""

    def __init__(self, message: str = "资源冲突", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=409, detail=detail)
