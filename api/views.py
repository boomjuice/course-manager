from django.db.models import Count, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDay
from datetime import date, timedelta, datetime, time
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, serializers, views, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .models import (
    Campus, Classroom, Teacher, Student, ScheduleEntry,
    DataDictionary, CourseProduct, Enrollment, Attendance, CourseOffering
)
from .serializers import (
    CampusSerializer, 
    ClassroomSerializer, TeacherSerializer, StudentSerializer, 
    ScheduleEntryListSerializer, ScheduleEntryCreateUpdateSerializer,
    DataDictionarySerializer, CourseProductSerializer, EnrollmentSerializer,
    AttendanceSerializer, CourseOfferingSerializer
)

class AuditMixin:
    """
    A mixin for ViewSets to automatically add created_by and updated_by usernames.
    """
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username, updated_by=self.request.user.username)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.username)

class CampusViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    permission_classes = [IsAdminOrReadOnly]


class DataDictionaryViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = DataDictionary.objects.all()
    serializer_class = DataDictionarySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        group_code = self.request.query_params.get('group_code')
        if group_code:
            queryset = queryset.filter(group_code=group_code)
        return queryset


class CourseProductFilter(filters.FilterSet):
    class Meta:
        model = CourseProduct
        fields = ['subject', 'grade', 'course_type']

class CourseProductViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = CourseProduct.objects.all()
    serializer_class = CourseProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = CourseProductFilter


class CourseOfferingFilter(filters.FilterSet):
    start_date__gte = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date__lte = filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date__gte = filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date__lte = filters.DateFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = CourseOffering
        fields = ['course_product', 'status', 'start_date__gte', 'start_date__lte', 'end_date__gte', 'end_date__lte']

class CourseOfferingViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = CourseOffering.objects.all().select_related('course_product')
    serializer_class = CourseOfferingSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = CourseOfferingFilter
    search_fields = ['name']

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'planning':
            return Response({'error': '只有“计划中”的开班计划才能被修改。'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'planning':
            return Response({'error': '只有“计划中”的开班计划才能被修改。'}, status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)


class EnrollmentFilter(filters.FilterSet):
    student__name__icontains = filters.CharFilter(field_name='student__name', lookup_expr='icontains')
    course_offering__name__icontains = filters.CharFilter(field_name='course_offering__name', lookup_expr='icontains')
    created_time__date__gte = filters.DateFilter(field_name='created_time', lookup_expr='date__gte')
    created_time__date__lte = filters.DateFilter(field_name='created_time', lookup_expr='date__lte')

    class Meta:
        model = Enrollment
        fields = ['student', 'course_offering', 'student__name__icontains', 'course_offering__name__icontains', 'created_time__date__gte', 'created_time__date__lte']

class EnrollmentViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Enrollment.objects.all().select_related('student', 'course_offering__course_product')
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = EnrollmentFilter

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        enrollment_ids_str = request.query_params.get('enrollment_ids')
        if not enrollment_ids_str:
            return Response({'error': 'enrollment_ids parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment_ids = [int(id) for id in enrollment_ids_str.split(',')]
        
        base_enrollments = Enrollment.objects.filter(id__in=enrollment_ids).select_related('student', 'course_offering')
        if not base_enrollments.exists():
            return Response({'error': 'No valid enrollments found for given IDs'}, status=status.HTTP_404_NOT_FOUND)

        # Assume all selected enrollments are in the same offering
        target_offering = base_enrollments.first().course_offering
        
        # Get the IDs of all students already selected
        selected_student_ids = [e.student.id for e in base_enrollments]
        
        # Get the IDs of all tags associated with the selected students
        shared_tag_ids = Student.objects.filter(id__in=selected_student_ids).values_list('tags__id', flat=True)
        
        # If the selected students have no tags, we cannot make a recommendation based on tags.
        if not shared_tag_ids:
            return Response([])

        # Find other enrollments in the same offering whose students share at least one tag
        recommended_enrollments = Enrollment.objects.filter(
            course_offering=target_offering,
            student__tags__id__in=list(set(shared_tag_ids))
        ).exclude(student__id__in=selected_student_ids).distinct()

        serializer = self.get_serializer(recommended_enrollments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='consumption-history')
    def consumption_history(self, request, pk=None):
        enrollment = self.get_object()
        # Find all completed schedule entries linked to this enrollment
        history = ScheduleEntry.objects.filter(
            enrollments=enrollment,
            status='completed'
        ).order_by('-end_time')

        # Paginate the results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(history, request)
        
        # We can create a simple serializer for this on the fly or a dedicated one
        data = [
            {
                'date': entry.end_time.strftime('%Y-%m-%d %H:%M'),
                'course_name': entry.course_name,
                'teacher_name': entry.teacher_name,
                'lessons_consumed': entry.lessons_consumed
            } for entry in page
        ]
        
        return paginator.get_paginated_response(data)


class AttendanceViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Attendance.objects.all().select_related('student', 'schedule_entry')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrReadOnly]


class ClassroomViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [IsAdminOrReadOnly]

class TeacherFilter(filters.FilterSet):
    subjects = filters.ModelChoiceFilter(queryset=DataDictionary.objects.filter(group_code='subjects'))
    grades = filters.ModelChoiceFilter(queryset=DataDictionary.objects.filter(group_code='grades'))

    class Meta:
        model = Teacher
        fields = ['subjects', 'grades']

class TeacherViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Teacher.objects.all().select_related('user').prefetch_related('subjects', 'grades')
    serializer_class = TeacherSerializer
    permission_classes = [IsOwnerOrAdmin]
    filterset_class = TeacherFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

class StudentFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__id',
        to_field_name='id',
        queryset=DataDictionary.objects.filter(group_code='student_tags')
    )

    class Meta:
        model = Student
        fields = ['grade', 'tags']
class StudentViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Student.objects.all().select_related('grade').prefetch_related('tags')
    serializer_class = StudentSerializer
    permission_classes = [IsOwnerOrAdmin]
    filterset_class = StudentFilter
    search_fields = ['name', 'school']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return super().get_queryset()
        
        if hasattr(user, 'student'):
             return super().get_queryset().filter(user=user)
        
        return Student.objects.none()

class ScheduleEntryViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = ScheduleEntry.objects.all().order_by('start_time')

    def get_queryset(self):
        queryset = super().get_queryset().select_related('classroom').prefetch_related('students', 'enrollments')
        
        teacher_name = self.request.query_params.get('teacher_name')
        student_name = self.request.query_params.get('student_name')
        classroom_id = self.request.query_params.get('classroom_id')
        subject_name = self.request.query_params.get('subject_name')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if teacher_name:
            queryset = queryset.filter(teacher_name__icontains=teacher_name)
        if student_name:
            queryset = queryset.filter(students__name__icontains=student_name).distinct()
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        if subject_name:
            queryset = queryset.filter(subject_name__icontains=subject_name)
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__date__lte=end_date)

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset
        elif hasattr(user, 'teacher'):
            return queryset.filter(teacher_id=user.teacher.id)
        elif hasattr(user, 'student'):
            return queryset.filter(students=user.student)
        return ScheduleEntry.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ScheduleEntryListSerializer
        return ScheduleEntryCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username, updated_by=self.request.user.username)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        read_serializer = ScheduleEntryListSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request, *args, **kwargs):
        # This is a custom action and requires a custom validation logic
        # instead of relying solely on the serializer for the whole process.
        data = request.data
        required_fields = ['enrollment_ids', 'teacher_id', 'classroom', 'start_time', 'end_time', 'start_date', 'end_date', 'days_of_week']
        if not all(field in data for field in required_fields):
            return Response({'error': 'Missing one or more required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            enrollments = Enrollment.objects.filter(id__in=data['enrollment_ids'])
            if not enrollments.exists():
                return Response({'error': 'No valid enrollments found.'}, status=status.HTTP_400_BAD_REQUEST)
            
            teacher = Teacher.objects.get(id=data['teacher_id'])
            classroom = Classroom.objects.get(id=data['classroom'])
            
            start_date = date.fromisoformat(data['start_date'])
            end_date = date.fromisoformat(data['end_date'])
            start_time = time.fromisoformat(data['start_time'])
            end_time = time.fromisoformat(data['end_time'])
            days_of_week = data['days_of_week']

        except (Enrollment.DoesNotExist, Teacher.DoesNotExist, Classroom.DoesNotExist, ValueError) as e:
            return Response({'error': f"Invalid input data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare data for snapshot fields
        first_product = enrollments.first().course_offering.course_product
        snapshot_data = {
            'teacher_id': teacher.id,
            'teacher_name': teacher.name,
            'classroom_name': classroom.name,
            'course_name': first_product.display_name,
            'subject_name': first_product.subject,
            'grade_name': first_product.grade,
        }

        entries_to_create = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in days_of_week:
                start_datetime = timezone.make_aware(datetime.combine(current_date, start_time))
                end_datetime = timezone.make_aware(datetime.combine(current_date, end_time))
                
                entry_data = {
                    'classroom': classroom,
                    'start_time': start_datetime,
                    'end_time': end_datetime,
                    'enrollments': enrollments,
                    **snapshot_data
                }
                entries_to_create.append(entry_data)
            current_date += timedelta(days=1)

        if not entries_to_create:
            return Response({'message': 'No schedule entries to create within the given date range and rules.'}, status=status.HTTP_200_OK)

        # Validate all potential entries before creating any
        all_valid = True
        errors = []
        for entry_data in entries_to_create:
            # We need a custom validation logic here that can be reused.
            # For now, let's adapt the serializer's validation logic.
            # This is a simplified version for demonstration. A refactored validation service would be ideal.
            # Simplified check:
            if ScheduleEntry.objects.filter(classroom=classroom, start_time__lt=entry_data['end_time'], end_time__gt=entry_data['start_time']).exists():
                 errors.append(f"Classroom conflict on {entry_data['start_time'].strftime('%Y-%m-%d')}")
                 all_valid = False
            if ScheduleEntry.objects.filter(teacher_id=teacher.id, start_time__lt=entry_data['end_time'], end_time__gt=entry_data['start_time']).exists():
                 errors.append(f"Teacher conflict on {entry_data['start_time'].strftime('%Y-%m-%d')}")
                 all_valid = False

        if not all_valid:
            return Response({'error': 'One or more conflicts detected.', 'details': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Create entries in a transaction
        try:
            with transaction.atomic():
                created_entries = []
                for entry_data in entries_to_create:
                    enrollment_ids = entry_data.pop('enrollments')
                    entry = ScheduleEntry.objects.create(**entry_data)
                    entry.enrollments.set(enrollment_ids)
                    entry.students.set(Student.objects.filter(enrollment__id__in=enrollment_ids).distinct())
                    created_entries.append(entry)
            
            read_serializer = ScheduleEntryListSerializer(created_entries, many=True)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f"An error occurred during creation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response({'error': 'Invalid data format. "ids" should be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                queryset = ScheduleEntry.objects.filter(id__in=ids)
                if queryset.count() != len(set(ids)):
                    return Response({'error': 'One or more specified IDs were not found.'}, status=status.HTTP_404_NOT_FOUND)
                
                deleted_count, _ = queryset.delete()

        except Exception as e:
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'status': 'success', 'deleted_count': deleted_count},
            status=status.HTTP_200_OK
        )


class DashboardStatsView(views.APIView):
    """
    Provides statistics for the dashboard based on user role.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Default to the current week if no dates are provided
        today = timezone.now().date()
        start_date_str = request.query_params.get('start_date', (today - timedelta(days=today.weekday())).isoformat())
        end_date_str = request.query_params.get('end_date', (today + timedelta(days=6 - today.weekday())).isoformat())

        # Basic validation for date format
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            end_date = datetime.fromisoformat(end_date_str).date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        # Base queryset for schedule entries within the date range
        schedule_entries = ScheduleEntry.objects.filter(
            start_time__date__gte=start_date,
            end_time__date__lte=end_date
        )

        user = self.request.user
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'role': 'pending',
            'stats': {}
        }

        if user.is_staff or user.is_superuser:
            data['role'] = 'admin'
            data['stats'] = self.get_admin_stats(schedule_entries, start_date, end_date)
        elif hasattr(user, 'teacher'):
            data['role'] = 'teacher'
            teacher_entries = schedule_entries.filter(teacher_id=user.teacher.id)
            data['stats'] = self.get_teacher_stats(teacher_entries)
        elif hasattr(user, 'student'):
            data['role'] = 'student'
            student_entries = schedule_entries.filter(students=user.student)
            data['stats'] = self.get_student_stats(user.student, student_entries)
        else:
            return Response({'error': 'User has no associated role.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(data)

    def get_student_stats(self, student, student_entries):
        # 1. KPIs
        course_count = student_entries.count()

        total_hours = student_entries.annotate(
            duration=ExpressionWrapper(F('end_time') - F('start_time'), output_field=fields.DurationField())
        ).aggregate(total_duration=Sum('duration'))['total_duration'] or timedelta(0)

        # This is a non-trivial calculation. It's better to calculate it based on all enrollments,
        # not just the schedule in the current date range.
        enrollments = Enrollment.objects.filter(student=student)
        total_lessons = enrollments.aggregate(total=Sum('total_lessons'))['total'] or 0
        used_lessons = enrollments.aggregate(total=Sum('used_lessons'))['total'] or 0
        remaining_lessons = total_lessons - used_lessons

        # Attendance Rate
        attended_count = Attendance.objects.filter(
            student=student,
            schedule_entry__in=student_entries,
            status='present'
        ).count()
        
        total_attended_or_absent = Attendance.objects.filter(
            student=student,
            schedule_entry__in=student_entries,
            status__in=['present', 'absent']
        ).count()

        attendance_rate = (attended_count / total_attended_or_absent * 100) if total_attended_or_absent > 0 else 100

        return {
            'kpis': {
                'course_count': course_count,
                'total_hours': round(total_hours.total_seconds() / 3600, 2),
                'remaining_lessons': remaining_lessons,
                'attendance_rate': round(attendance_rate, 2)
            }
        }

    def get_teacher_stats(self, teacher_entries):
        # 1. KPIs
        total_hours = teacher_entries.annotate(
            duration=ExpressionWrapper(F('end_time') - F('start_time'), output_field=fields.DurationField())
        ).aggregate(total_duration=Sum('duration'))['total_duration'] or timedelta(0)

        course_count = teacher_entries.count()
        
        student_count = teacher_entries.aggregate(
            total_students=Count('students')
        )['total_students']

        # 2. Subject distribution
        subject_distribution = teacher_entries.values('subject_name').annotate(
            course_count=Count('id')
        ).order_by('-course_count')

        return {
            'kpis': {
                'total_hours': round(total_hours.total_seconds() / 3600, 2),
                'course_count': course_count,
                'student_count': student_count,
            },
            'charts': {
                'subject_distribution': list(subject_distribution),
            }
        }

    def get_admin_stats(self, schedule_entries, start_date, end_date):
        # 1. KPIs
        total_scheduled_hours = schedule_entries.annotate(
            duration=ExpressionWrapper(F('end_time') - F('start_time'), output_field=fields.DurationField())
        ).aggregate(total_duration=Sum('duration'))['total_duration'] or timedelta(0)

        active_teachers_count = schedule_entries.values('teacher_id').distinct().count()
        
        student_attendance_count = schedule_entries.aggregate(
            total_students=Count('students')
        )['total_students']

        completed_courses_count = schedule_entries.filter(status='completed').count()

        # 2. Course hours distribution
        course_hours_distribution = schedule_entries.annotate(
            date=TruncDay('start_time')
        ).values('date').annotate(
            daily_hours=Sum(ExpressionWrapper(F('end_time') - F('start_time'), output_field=fields.DurationField()))
        ).order_by('date')

        # Convert duration to hours
        distribution_data = [
            {
                'date': item['date'].strftime('%Y-%m-%d'),
                'hours': item['daily_hours'].total_seconds() / 3600 if item['daily_hours'] else 0
            } for item in course_hours_distribution
        ]

        # 3. Popular course products
        popular_courses = schedule_entries.values('course_name').annotate(
            entry_count=Count('id')
        ).order_by('-entry_count')[:5]

        # 4. Teacher workload ranking
        teacher_workload = schedule_entries.values('teacher_name').annotate(
            work_hours=Sum(ExpressionWrapper(F('end_time') - F('start_time'), output_field=fields.DurationField()))
        ).order_by('-work_hours')[:10]
        
        teacher_workload_data = [
            {
                'teacher_name': item['teacher_name'],
                'hours': item['work_hours'].total_seconds() / 3600 if item['work_hours'] else 0
            } for item in teacher_workload
        ]

        return {
            'kpis': {
                'total_scheduled_hours': round(total_scheduled_hours.total_seconds() / 3600, 2),
                'active_teachers_count': active_teachers_count,
                'student_attendance_count': student_attendance_count,
                'completed_courses_count': completed_courses_count,
            },
            'charts': {
                'course_hours_distribution': distribution_data,
                'popular_courses': list(popular_courses),
                'teacher_workload': teacher_workload_data,
            }
        }
