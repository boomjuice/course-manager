from datetime import date, timedelta, datetime
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin, IsTeacherOrAdminOrReadOnly
from .models import (
    Campus, Subject, Grade, Tag, Classroom, Teacher, Student, TeachingClass, ScheduleEntry, TimeSlot
)
from .serializers import (
    CampusSerializer, SubjectSerializer, GradeSerializer, TagSerializer, 
    ClassroomSerializer, TeacherSerializer, StudentSerializer, TeachingClassSerializer, 
    ScheduleEntryListSerializer, ScheduleEntryCreateUpdateSerializer, TimeSlotSerializer
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

class SubjectViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]

class GradeViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAdminOrReadOnly]

class TagViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]

class ClassroomViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [IsAdminOrReadOnly]

class TimeSlotViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAdminOrReadOnly]

class TeacherViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Teacher.objects.all().prefetch_related('subjects', 'grades')
        return Teacher.objects.filter(user=user).prefetch_related('subjects', 'grades')

class StudentViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = Student.objects.all().prefetch_related('tags')
        
        tags_param = self.request.query_params.get('tags')
        if tags_param:
            tag_ids = [int(tag_id) for tag_id in tags_param.split(',')]
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset
        
        if hasattr(user, 'student'):
             return queryset.filter(user=user)
        
        return Student.objects.none()

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        teaching_class_id = request.query_params.get('teaching_class_id')
        if not teaching_class_id:
            return Response({'error': 'teaching_class_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            teaching_class = TeachingClass.objects.get(id=teaching_class_id)
        except TeachingClass.DoesNotExist:
            return Response({'error': 'TeachingClass not found'}, status=status.HTTP_404_NOT_FOUND)

        existing_student_ids = teaching_class.students.values_list('id', flat=True)
        tags = Tag.objects.filter(student__in=existing_student_ids).distinct()

        recommended_students = Student.objects.filter(tags__in=tags).exclude(id__in=existing_student_ids).distinct()

        serializer = self.get_serializer(recommended_students, many=True)
        return Response(serializer.data)

class TeachingClassViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = TeachingClassSerializer
    permission_classes = [IsTeacherOrAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return TeachingClass.objects.all().select_related('teacher', 'subject', 'grade').prefetch_related('students')
        elif hasattr(user, 'teacher'):
            return TeachingClass.objects.filter(teacher=user.teacher).select_related('teacher', 'subject', 'grade').prefetch_related('students')
        elif hasattr(user, 'student'):
            return TeachingClass.objects.filter(students=user.student).select_related('teacher', 'subject', 'grade').prefetch_related('students')
        return TeachingClass.objects.none()

class ScheduleEntryViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = ScheduleEntry.objects.all().order_by('start_time')

    def get_queryset(self):
        queryset = super().get_queryset()
        
        teacher_id = self.request.query_params.get('teacher')
        student_id = self.request.query_params.get('student')
        classroom_id = self.request.query_params.get('classroom')
        subject_id = self.request.query_params.get('subject')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if teacher_id:
            queryset = queryset.filter(teaching_class__teacher_id=teacher_id)
        if student_id:
            queryset = queryset.filter(teaching_class__students__id=student_id)
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        if subject_id:
            queryset = queryset.filter(teaching_class__subject_id=subject_id)
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__date__lte=end_date)

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset
        elif hasattr(user, 'teacher'):
            return queryset.filter(teaching_class__teacher=user.teacher)
        elif hasattr(user, 'student'):
            return queryset.filter(teaching_class__students__user=user)
        return ScheduleEntry.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ScheduleEntryListSerializer
        return ScheduleEntryCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        
        read_serializer = ScheduleEntryListSerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request):
        teaching_class_id = request.data.get('teaching_class_id')
        classroom_id = request.data.get('classroom_id')
        timeslot_id = request.data.get('timeslot_id')
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        days_of_week = request.data.get('days_of_week', [])

        if not all([teaching_class_id, classroom_id, timeslot_id, start_date_str, end_date_str]):
            return Response({'error': 'Missing required parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            teaching_class = TeachingClass.objects.get(id=teaching_class_id)
            classroom = Classroom.objects.get(id=classroom_id)
            timeslot = TimeSlot.objects.get(id=timeslot_id)
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except (TeachingClass.DoesNotExist, Classroom.DoesNotExist, TimeSlot.DoesNotExist, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        entries_to_create = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in days_of_week:
                start_time = timezone.make_aware(datetime.combine(current_date, timeslot.start_time))
                end_time = timezone.make_aware(datetime.combine(current_date, timeslot.end_time))
                entries_to_create.append({
                    'teaching_class': teaching_class,
                    'classroom': classroom,
                    'start_time': start_time,
                    'end_time': end_time,
                })
            current_date += timedelta(days=1)

        if not entries_to_create:
            return Response({'status': 'no_op', 'message': 'No valid days found.'}, status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                for entry_data in entries_to_create:
                    serializer = ScheduleEntryCreateUpdateSerializer(data={
                        'teaching_class': entry_data['teaching_class'].id,
                        'classroom': entry_data['classroom'].id,
                        'start_time': entry_data['start_time'],
                        'end_time': entry_data['end_time'],
                    })
                    serializer.is_valid(raise_exception=True)
                
                ScheduleEntry.objects.bulk_create(
                    [ScheduleEntry(**data, created_by=request.user.username, updated_by=request.user.username) for data in entries_to_create]
                )

        except serializers.ValidationError as e:
            conflicting_time = "unknown time"
            for entry in entries_to_create:
                try:
                    temp_serializer = ScheduleEntryCreateUpdateSerializer(data={
                        'teaching_class': entry['teaching_class'].id,
                        'classroom': entry['classroom'].id,
                        'start_time': entry['start_time'],
                        'end_time': entry['end_time'],
                    })
                    temp_serializer.is_valid(raise_exception=True)
                except serializers.ValidationError:
                    conflicting_time = entry['start_time'].strftime('%Y-%m-%d %H:%M')
                    break
            
            error_detail = e.detail
            error_message = f"在 {conflicting_time} 的排课存在冲突: {str(error_detail)}"
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'status': 'success', 'created_count': len(entries_to_create)},
            status=status.HTTP_201_CREATED
        )

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
