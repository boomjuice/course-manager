"""
SQLAlchemy models package.
"""
from app.models.base import BaseModel
from app.models.user import User, LoginLog, Role
from app.models.dictionary import DictType, DictItem
from app.models.campus import Campus, Classroom
from app.models.course import Course
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class_plan import ClassPlan
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule
from app.models.lesson_record import LessonRecord
from app.models.student_attendance import StudentAttendance
from app.models.permission import Resource, Permission, UserRole, RolePermission

__all__ = [
    "BaseModel",
    "User",
    "LoginLog",
    "Role",
    "DictType",
    "DictItem",
    "Campus",
    "Classroom",
    "Course",
    "Student",
    "Teacher",
    "ClassPlan",
    "Enrollment",
    "Schedule",
    "LessonRecord",
    "StudentAttendance",
    # RBAC权限模型
    "Resource",
    "Permission",
    "UserRole",
    "RolePermission",
]
