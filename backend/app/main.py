"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import CourseManagerException
from app.core.scheduler import start_scheduler, shutdown_scheduler, get_scheduler_status
from app.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}...")
    await init_db()
    print("Database initialized")

    # 启动定时任务调度器
    start_scheduler()
    print("Scheduler started")

    yield

    # Shutdown
    print("Shutting down...")
    shutdown_scheduler()
    print("Scheduler stopped")
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="课程管理系统 API - 现代化教育培训管理平台",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(CourseManagerException)
async def course_manager_exception_handler(
    request: Request,
    exc: CourseManagerException
) -> JSONResponse:
    """Handle custom application exceptions. 统一返回 ResponseModel 格式."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "data": None,
            "rows": None,
            "detail": exc.detail,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions. 统一返回 ResponseModel 格式."""
    if settings.debug:
        import traceback
        detail = traceback.format_exc()
    else:
        detail = None

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "rows": None,
            "detail": detail,
        }
    )


# Include API router
app.include_router(api_router)


# Health check endpoint
@app.get("/health", tags=["健康检查"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "scheduler": get_scheduler_status(),
    }


@app.get("/", tags=["首页"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
