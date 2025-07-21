from rest_framework import serializers
from .models import (
    Campus, Classroom, Teacher, Student,
    ScheduleEntry, CourseProduct, DataDictionary, Enrollment, Attendance, CourseOffering
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

class DataDictionarySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = DataDictionary
        fields = ['id', 'group_code', 'item_value', 'subgroup', 'sort_order', 'created_time', 'updated_time', 'created_by', 'updated_by']

class CourseProductSerializer(BaseSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = CourseProduct
        fields = ['id', 'subject', 'grade', 'course_type', 'duration_minutes', 'display_name', 'created_time', 'updated_time', 'created_by', 'updated_by']

class StudentSerializer(BaseSerializer):
    tags = DataDictionarySerializer(many=True, read_only=True)
    grade = DataDictionarySerializer(read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=DataDictionary.objects.filter(group_code='student_tags'),
        source='tags', many=True, write_only=True, required=False
    )
    grade_id = serializers.PrimaryKeyRelatedField(
        queryset=DataDictionary.objects.filter(group_code='grades'),
        source='grade', write_only=True, required=False, allow_null=True
    )

    class Meta(BaseSerializer.Meta):
        model = Student
        fields = [
            'id', 'name', 'school', 'grade', 'parent_contact_info', 'tags', 
            'is_active', 'tag_ids', 'notes', 'grade_id',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]

    def create(self, validated_data):
        from pypinyin import pinyin, Style
        import re

        # Generate a unique username
        base_username = "".join(item[0] for item in pinyin(validated_data['name'], style=Style.NORMAL))
        base_username = re.sub(r'[^a-zA-Z0-9]', '', base_username).lower()
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user with a default password
        user = User.objects.create_user(username=username, password="123456")

        # Add user to the 'student_group'
        try:
            student_group = Group.objects.get(name='student_group')
            user.groups.add(student_group)
        except Group.DoesNotExist:
            # In a real application, you might want to log this or handle it differently
            pass

        validated_data['user'] = user
        return super().create(validated_data)

class CourseOfferingSerializer(BaseSerializer):
    course_product = CourseProductSerializer(read_only=True)
    course_product_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseProduct.objects.all(), source='course_product', write_only=True
    )
    display_name = serializers.CharField(read_only=True)
    enrollment_count = serializers.IntegerField(source='enrollment_set.count', read_only=True)
    enrolled_students = StudentSerializer(source='get_enrolled_students', many=True, read_only=True)


    class Meta(BaseSerializer.Meta):
        model = CourseOffering
        fields = [
            'id', 'name', 'start_date', 'end_date', 'status', 
            'course_product', 'course_product_id', 'display_name',
            'enrollment_count', 'enrolled_students',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]

class ClassroomSerializer(BaseSerializer):
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    class Meta(BaseSerializer.Meta):
        model = Classroom
        fields = ['id', 'name', 'capacity', 'campus', 'campus_name', 'is_active', 'created_time', 'updated_time', 'created_by', 'updated_by']

class TeacherSerializer(BaseSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    name = serializers.CharField(required=True) # Make teacher's name required
    
    subjects = DataDictionarySerializer(many=True, read_only=True)
    grades = DataDictionarySerializer(many=True, read_only=True)
    subject_ids = serializers.PrimaryKeyRelatedField(
        queryset=DataDictionary.objects.filter(group_code='subjects'), source='subjects', many=True, write_only=True
    )
    grade_ids = serializers.PrimaryKeyRelatedField(
        queryset=DataDictionary.objects.filter(group_code='grades'), source='grades', many=True, write_only=True
    )

    class Meta(BaseSerializer.Meta):
        model = Teacher
        fields = [
            'id', 'user_id', 'password', 'name', 'contact_info',
            'subjects', 'grades', 'subject_ids', 'grade_ids',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]

    def create(self, validated_data):
        # Username will be generated automatically, so it's removed from here.
        password = validated_data.pop('password', "123456") # Default password

        # User creation logic will be moved to a more robust place,
        # likely involving pinyin generation. For now, this is simplified.
        from pypinyin import pinyin, Style
        import re

        # Generate a unique username
        base_username = "".join(item[0] for item in pinyin(validated_data['name'], style=Style.NORMAL))
        base_username = re.sub(r'[^a-zA-Z0-9]', '', base_username).lower()
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(username=username, password=password)

        # Add user to the 'teacher_group'
        try:
            teacher_group = Group.objects.get(name='teacher_group')
            user.groups.add(teacher_group)
        except Group.DoesNotExist:
            pass

        subjects = validated_data.pop('subjects', [])
        grades = validated_data.pop('grades', [])

        teacher = Teacher.objects.create(user=user, **validated_data)
        teacher.subjects.set(subjects)
        teacher.grades.set(grades)
        return teacher

    def update(self, instance, validated_data):
        # Username is not updatable
        validated_data.pop('password', None) # Password changes should have a dedicated endpoint

        subjects = validated_data.pop('subjects', None)
        grades = validated_data.pop('grades', None)

        # Update teacher fields
        instance.name = validated_data.get('name', instance.name)
        instance.contact_info = validated_data.get('contact_info', instance.contact_info)
        instance.save()

        if subjects is not None:
            instance.subjects.set(subjects)
        if grades is not None:
            instance.grades.set(grades)

        return instance


class EnrollmentSerializer(BaseSerializer):
    student = StudentSerializer(read_only=True)
    course_offering = CourseOfferingSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='student', write_only=True
    )
    course_offering_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseOffering.objects.all(), source='course_offering', write_only=True
    )
    display_name = serializers.CharField(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Enrollment
        fields = [
            'id', 'student', 'course_offering', 
            'total_lessons', 'used_lessons', 'student_id', 'course_offering_id',
            'display_name',
            'created_time', 'updated_time', 'created_by', 'updated_by'
        ]

class AttendanceSerializer(BaseSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    schedule_entry_info = serializers.CharField(source='schedule_entry.__str__', read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Attendance
        fields = '__all__'

class ScheduleEntryListSerializer(BaseSerializer):
    students = StudentSerializer(many=True, read_only=True)
    enrollments = EnrollmentSerializer(many=True, read_only=True)
    classroom = ClassroomSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)

    class Meta(BaseSerializer.Meta):
        model = ScheduleEntry
        fields = '__all__'

class ScheduleEntryCreateUpdateSerializer(BaseSerializer):
    enrollment_ids = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source='enrollments', many=True, write_only=True, required=False
    )

    class Meta(BaseSerializer.Meta):
        model = ScheduleEntry
        fields = [
            'id', 'classroom', 'start_time', 'end_time', 'status', 
            'enrollment_ids', 'teacher_id', 'teacher_name',
            'course_name', 'subject_name', 'grade_name',
            'lessons_consumed', 'notes'
        ]

    def create(self, validated_data):
        enrollments_data = validated_data.pop('enrollments')
        
        schedule_entry = ScheduleEntry.objects.create(**validated_data)
        schedule_entry.enrollments.set(enrollments_data)

        students = Student.objects.filter(enrollment__in=enrollments_data).distinct()
        schedule_entry.students.set(students)
        
        return schedule_entry

    def validate(self, data):
        # Skip enrollment validation on partial update (PATCH)
        if self.partial:
            return data

        start_time = data.get('start_time')
        end_time = data.get('end_time')
        classroom = data.get('classroom')
        enrollments = data.get('enrollments')
        teacher_id = data.get('teacher_id')

        if not enrollments:
            raise serializers.ValidationError("At least one enrollment is required.")

        # All enrollments must belong to the same course offering
        offering_ids = {e.course_offering.id for e in enrollments}
        if len(offering_ids) > 1:
            raise serializers.ValidationError({'enrollment_ids': "所有报名记录必须属于同一个开班计划。"})

        course_offering = enrollments[0].course_offering
        if not (course_offering.start_date <= start_time.date() <= course_offering.end_date):
            raise serializers.ValidationError({
                'start_time': f"排课日期必须在开班计划的有效日期范围内 ({course_offering.start_date} to {course_offering.end_date})。"
            })

        # Check for one-on-one course type conflict
        product_types = {e.course_offering.course_product.course_type for e in enrollments}
        if 'one_on_one' in product_types and len(enrollments) > 1:
            raise serializers.ValidationError({'enrollment_ids': "一对一课程只能选择一个报名记录。"})

        queryset = ScheduleEntry.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        errors = {}

        if classroom and queryset.filter(classroom=classroom, start_time__lt=end_time, end_time__gt=start_time).exists():
            errors['classroom'] = "该教室在此时间段已被预定。"

        student_ids = [e.student.id for e in enrollments]
        student_conflicts = queryset.filter(
            students__id__in=student_ids,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).distinct()

        if student_conflicts.exists():
            conflicting_students = Student.objects.filter(id__in=student_conflicts.values_list('students__id', flat=True))
            student_names = ", ".join([s.name for s in conflicting_students])
            errors['student_conflict'] = f"学生 {student_names} 在此时间段已有课程安排。"

        if teacher_id and queryset.filter(teacher_id=teacher_id, start_time__lt=end_time, end_time__gt=start_time).exists():
            errors['teacher_id'] = "该教师在此时间段已有课程安排。"

        if errors:
            raise serializers.ValidationError(errors)

        return data
