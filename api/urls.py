from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    CampusViewSet, SubjectViewSet, GradeViewSet, TagViewSet, 
    ClassroomViewSet, TeacherViewSet, StudentViewSet, TeachingClassViewSet, 
    ScheduleEntryViewSet, TimeSlotViewSet
)

router = DefaultRouter()
router.register(r'campuses', CampusViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'classrooms', ClassroomViewSet)
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teaching-classes', TeachingClassViewSet, basename='teaching_class')
router.register(r'schedule-entries', ScheduleEntryViewSet, basename='schedule_entry')
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
]
