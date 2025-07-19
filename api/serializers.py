from rest_framework import serializers
from .models import (
    Campus, Subject, Grade, Tag, Classroom, Teacher, Student, 
    TeachingClass, ScheduleEntry, TimeSlot
)
from django.utils import timezone
from django.contrib.auth.models import User, Group

class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        read_only_fields = ('created_time', 'updated_time', 'created_by', 'updated_by')

class CampusSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Campus
        fields = '__all__'

class SubjectSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Subject
        fields = '__all__'

class GradeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = Grade
        fields = '__all__'

class TagSerializer(BaseSerializer):
    group_display = serializers.CharField(source='get_group_display', read_only=True)
    class Meta(BaseSerializer.Meta):
        model = Tag
        fields = ['id', 'name', 'group', 'group_display', 'created_time', 'updated_time', 'created_by', 'updated_by']

class ClassroomSerializer(BaseSerializer):
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    class Meta(BaseSerializer.Meta):
        model = Classroom
        fields = ['id', 'name', 'capacity', 'campus', 'campus_name', 'is_active', 'created_time', 'updated_time', 'created_by', 'updated_by']

class TimeSlotSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = TimeSlot
        fields = '__all__'

class TeacherSerializer(BaseSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    grades = GradeSerializer(many=True, read_only=True)
    
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    subject_ids = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source='subjects', many=True, write_only=True, required=False
    )
    grade_ids = serializers.PrimaryKeyRelatedField(
        queryset=Grade.objects.all(), source='grades', many=True, write_only=True, required=False
    )

    class Meta(BaseSerializer.Meta):
        model = Teacher
        fields = [
            'id', 'user', 'user_name', 'contact_info', 'subjects', 'grades', 'is_active',
            'username', 'password', 'subject_ids', 'grade_ids',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]
        read_only_fields = BaseSerializer.Meta.read_only_fields + ('user',)
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password', None)
        subjects_data = validated_data.pop('subjects', [])
        grades_data = validated_data.pop('grades', [])

        user = User.objects.create(username=username)
        if password:
            user.set_password(password)
        user.save()
        
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        user.groups.add(teacher_group)

        teacher = Teacher.objects.create(user=user, **validated_data)
        teacher.subjects.set(subjects_data)
        teacher.grades.set(grades_data)
        
        return teacher

    def update(self, instance, validated_data):
        subjects_data = validated_data.pop('subjects', None)
        grades_data = validated_data.pop('grades', None)
        
        if 'username' in validated_data:
            instance.user.username = validated_data.pop('username')
        
        if 'password' in validated_data:
            password = validated_data.pop('password')
            if password:
                instance.user.set_password(password)
        
        instance.user.save()

        instance.contact_info = validated_data.get('contact_info', instance.contact_info)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()

        if subjects_data is not None:
            instance.subjects.set(subjects_data)
        if grades_data is not None:
            instance.grades.set(grades_data)
            
        return instance

class StudentSerializer(BaseSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        write_only=True,
        required=False
    )

    class Meta(BaseSerializer.Meta):
        model = Student
        fields = ['id', 'name', 'parent_contact_info', 'tags', 'is_active', 'tag_ids', 'created_time', 'updated_time', 'created_by', 'updated_by']

class TeachingClassSerializer(BaseSerializer):
    teacher = TeacherSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    grade = GradeSerializer(read_only=True)
    students = StudentSerializer(many=True, read_only=True)
    
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source='teacher', write_only=True
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source='subject', write_only=True
    )
    grade_id = serializers.PrimaryKeyRelatedField(
        queryset=Grade.objects.all(), source='grade', write_only=True
    )
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='students', write_only=True, many=True
    )

    class Meta(BaseSerializer.Meta):
        model = TeachingClass
        fields = [
            'id', 'name', 'class_type', 'teacher', 'subject', 'grade', 'students',
            'teacher_id', 'subject_id', 'grade_id', 'student_ids', 'is_active',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]

class ScheduleEntryListSerializer(BaseSerializer):
    teaching_class = TeachingClassSerializer(read_only=True)
    classroom = ClassroomSerializer(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = ScheduleEntry
        fields = '__all__'

class ScheduleEntryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = [
            'teaching_class', 'classroom', 'start_time', 'end_time', 'status'
        ]

    def validate(self, data):
        """
        核心冲突检测逻辑。
        """
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        classroom = data.get('classroom')
        teaching_class = data.get('teaching_class')

        # 确保所有时间都是 aware 的
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)

        # 排除当前实例以支持更新操作
        queryset = ScheduleEntry.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        errors = {}

        # 1. 教室冲突
        if queryset.filter(classroom=classroom, start_time__lt=end_time, end_time__gt=start_time).exists():
            errors['classroom'] = "该教室在此时间段已被预定。"

        # 2. 教师冲突
        if queryset.filter(teaching_class__teacher=teaching_class.teacher, start_time__lt=end_time, end_time__gt=start_time).exists():
            errors['teacher'] = "该教师在此时间段已有课程安排。"

        # 3. 学生冲突
        student_conflicts = queryset.filter(
            teaching_class__students__in=teaching_class.students.all(),
            start_time__lt=end_time,
            end_time__gt=start_time
        ).distinct()

        if student_conflicts.exists():
            conflicting_students = []
            # 找出具体是哪个学生冲突
            for student in teaching_class.students.all():
                if queryset.filter(teaching_class__students=student, start_time__lt=end_time, end_time__gt=start_time).exists():
                    conflicting_students.append(student.name)
            if conflicting_students:
                errors[f'student_conflict'] = f"学生 {', '.join(conflicting_students)} 在此时间段已有课程安排。"

        if errors:
            raise serializers.ValidationError(errors)

        return data
