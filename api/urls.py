from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    CampusViewSet, 
    ClassroomViewSet, TeacherViewSet, StudentViewSet, 
    ScheduleEntryViewSet, DataDictionaryViewSet, CourseProductViewSet,
    EnrollmentViewSet, AttendanceViewSet, CourseOfferingViewSet,
    DashboardStatsView
)

router = DefaultRouter()
router.register(r'campuses', CampusViewSet)
router.register(r'classrooms', ClassroomViewSet)
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'schedule-entries', ScheduleEntryViewSet, basename='schedule_entry')
router.register(r'data-dictionary', DataDictionaryViewSet)
router.register(r'course-products', CourseProductViewSet)
router.register(r'course-offerings', CourseOfferingViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'attendances', AttendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]