"""
API v1 router aggregation.
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth, user, dictionary, campus, course,
    student, teacher, class_plan, enrollment, dashboard, schedule, lesson_record, scheduler,
    student_attendance, permission
)

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(user.login_logs_router)  # Global login logs
api_router.include_router(dictionary.router)
api_router.include_router(campus.router)
api_router.include_router(course.router)
api_router.include_router(student.router)
api_router.include_router(teacher.router)
api_router.include_router(class_plan.router)
api_router.include_router(enrollment.router)
api_router.include_router(schedule.router)
api_router.include_router(lesson_record.router)
api_router.include_router(dashboard.router)
api_router.include_router(scheduler.router)
api_router.include_router(student_attendance.router)
api_router.include_router(permission.router)  # RBAC权限管理
