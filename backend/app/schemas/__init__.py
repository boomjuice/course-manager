"""
Pydantic schemas package.
"""
from app.schemas.common import (
    ResponseModel,
    PaginatedResponse,
    MessageResponse,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TokenPayload,
    PasswordChangeRequest,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    LoginLogResponse,
)

__all__ = [
    # Common
    "ResponseModel",
    "PaginatedResponse",
    "MessageResponse",
    # Auth
    "LoginRequest",
    "TokenResponse",
    "TokenPayload",
    "PasswordChangeRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "LoginLogResponse",
]
