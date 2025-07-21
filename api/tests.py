from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    Campus, Classroom, Teacher, Student, ScheduleEntry,
    DataDictionary, CourseProduct, Enrollment, Attendance, CourseOffering
)
import datetime
from django.utils import timezone
from decimal import Decimal

# --- Existing Auth Test (No changes needed) ---
class AuthAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_failure(self):
        response = self.client.post('/api/auth/login/', {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)


# --- V2 API Tests ---

class V2_BaseTestCase(APITestCase):
    """A base test case for V2 APIs, providing common setup."""
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='password', is_staff=True)
        self.client.force_authenticate(user=self.admin_user)

        # Data Dictionary entries
        DataDictionary.objects.create(group_code='grades', item_value='G1')
        DataDictionary.objects.create(group_code='subjects', item_value='Math')
        DataDictionary.objects.create(group_code='course_types', item_value='one_on_one')
        DataDictionary.objects.create(group_code='course_types', item_value='small_group')
        DataDictionary.objects.create(group_code='student_tags', item_value='Needs Attention')

        # Core V2 Models
        self.product1 = CourseProduct.objects.create(
            subject="Math", grade="G1", 
            course_type="one_on_one", duration_minutes=60
        )
        self.product2 = CourseProduct.objects.create(
            subject="Math", grade="G1", 
            course_type="small_group", duration_minutes=90
        )
        
        self.student1 = Student.objects.create(name='Alice')
        self.student2 = Student.objects.create(name='Bob')

        self.offering1 = CourseOffering.objects.create(
            name="G1 Math 1-on-1 Fall",
            course_product=self.product1,
            start_date="2025-09-01",
            end_date="2026-01-15"
        )

        self.enrollment1 = Enrollment.objects.create(
            student=self.student1, course_offering=self.offering1, 
            total_lessons=10
        )
        self.enrollment2 = Enrollment.objects.create(
            student=self.student2, course_offering=self.offering1,
            total_lessons=20
        )
        
        self.campus = Campus.objects.create(name='Main Campus')
        self.classroom1 = Classroom.objects.create(name='Room 101', capacity=30, campus=self.campus)


class V2_DataApiTest(V2_BaseTestCase):
    def test_get_data_dictionary_no_filter(self):
        response = self.client.get('/api/data-dictionary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_get_data_dictionary_with_filter(self):
        response = self.client.get('/api/data-dictionary/?group_code=course_types')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertTrue(all(item['group_code'] == 'course_types' for item in response.data['results']))

    def test_course_product_crud(self):
        # Create
        data = {'subject': 'Physics', 'grade': 'G12', 'course_type': 'small_group', 'duration_minutes': 55}
        response = self.client.post('/api/course-products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CourseProduct.objects.count(), 3)
        
        # Read
        product_id = response.data['id']
        response = self.client.get(f'/api/course-products/{product_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subject'], 'Physics')

        # Update
        update_data = {'duration_minutes': 60}
        response = self.client.patch(f'/api/course-products/{product_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['duration_minutes'], 60)

        # Delete
        response = self.client.delete(f'/api/course-products/{product_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CourseProduct.objects.count(), 2)


class V2_ScheduleApiTest(V2_BaseTestCase):
    def setUp(self):
        super().setUp()
        self.start_time = timezone.make_aware(datetime.datetime(2025, 9, 1, 10, 0)) # Within offering range
        self.end_time = self.start_time + datetime.timedelta(minutes=60)
        self.teacher_user = User.objects.create_user(username='testteacher', password='password')
        self.teacher = Teacher.objects.create(user=self.teacher_user)

    def test_create_schedule_entry_success(self):
        data = {
            "enrollment_ids": [self.enrollment1.id],
            "teacher_id": self.teacher.id,
            "teacher_name": self.teacher.user.username,
            "classroom": self.classroom1.id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "course_name": "Auto-filled Course",
            "subject_name": "Auto-filled Subject",
            "grade_name": "Auto-filled Grade",
        }
        response = self.client.post('/api/schedule-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScheduleEntry.objects.count(), 1)
        
        entry = ScheduleEntry.objects.first()
        self.assertEqual(entry.teacher_id, self.teacher.id)
        self.assertTrue(entry.students.filter(id=self.student1.id).exists())

    def test_teacher_conflict(self):
        # Create an initial entry for the teacher
        ScheduleEntry.objects.create(
            teacher_id=self.teacher.id, teacher_name=self.teacher.user.username,
            classroom=self.classroom1, start_time=self.start_time, end_time=self.end_time,
        )
        # Attempt to create a conflicting entry for the same teacher
        data = {
            "enrollment_ids": [self.enrollment1.id],
            "teacher_id": self.teacher.id, # Same teacher
            "teacher_name": self.teacher.user.username,
            "classroom": Classroom.objects.create(name='Room 102', campus=self.campus, capacity=10).id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }
        response = self.client.post('/api/schedule-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('teacher_id', response.data)

    def test_student_conflict(self):
        # Create an entry for student1
        entry = ScheduleEntry.objects.create(
            classroom=self.classroom1, start_time=self.start_time, end_time=self.end_time,
        )
        entry.students.add(self.student1)

        # Attempt to create another entry for a group containing student1 at the same time
        data = {
            "enrollment_ids": [self.enrollment1.id], # This enrollment has student1
            "teacher_id": self.teacher.id,
            "teacher_name": self.teacher.user.username,
            "classroom": Classroom.objects.create(name='Room 102', campus=self.campus, capacity=10).id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }
        response = self.client.post('/api/schedule-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('student_conflict', response.data)


class V2_LessonDeductionSignalTest(V2_BaseTestCase):
    def test_lesson_deduction_on_completion(self):
        start_time = timezone.now() - datetime.timedelta(hours=2)
        end_time = start_time + datetime.timedelta(minutes=60) # 1 hour duration
        
        entry = ScheduleEntry.objects.create(
            start_time=start_time, end_time=end_time, status='scheduled',
            course_name=self.product1.display_name,
        )
        entry.enrollments.add(self.enrollment1)
        entry.students.add(self.student1)

        # Student was present
        Attendance.objects.create(schedule_entry=entry, student=self.student1, status='present')

        # Manually trigger the "completion"
        entry.status = 'completed'
        entry.save()

        # Check if lessons were deducted
        self.enrollment1.refresh_from_db()
        # duration (60) / standard_duration (60) = 1.0
        self.assertEqual(self.enrollment1.used_lessons, Decimal('1.00'))

    def test_no_deduction_for_absent_student(self):
        start_time = timezone.now() - datetime.timedelta(hours=2)
        end_time = start_time + datetime.timedelta(minutes=120) # 2 hour duration
        
        entry = ScheduleEntry.objects.create(
            start_time=start_time, end_time=end_time, status='scheduled',
            course_name=self.product2.display_name,
        )
        entry.enrollments.add(self.enrollment2)
        entry.students.add(self.student2)

        # Student was absent
        Attendance.objects.create(schedule_entry=entry, student=self.student2, status='absent')

        # Manually trigger the "completion"
        entry.status = 'completed'
        entry.save()

        # Check that lessons were NOT deducted
        self.enrollment2.refresh_from_db()
        self.assertEqual(self.enrollment2.used_lessons, Decimal('0.00'))


class V2_UserRelatedApiTest(V2_BaseTestCase):
    def test_create_teacher_with_subjects_and_grades(self):
        math_subject = DataDictionary.objects.get(item_value='Math')
        g1_grade = DataDictionary.objects.get(item_value='G1')
        
        data = {
            "name":"teacher1",
            "username": "newteacher",
            "password": "password123",
            "contact_info": "123456789",
            "subject_ids": [math_subject.id],
            "grade_ids": [g1_grade.id]
        }
        
        response = self.client.post('/api/teachers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        teacher = Teacher.objects.get(id=response.data['id'])
        self.assertEqual(teacher.subjects.count(), 1)
        self.assertEqual(teacher.subjects.first().item_value, 'Math')
        self.assertEqual(teacher.grades.count(), 1)
        self.assertEqual(teacher.grades.first().item_value, 'G1')

    def test_create_student_with_tags(self):
        tag = DataDictionary.objects.get(item_value='Needs Attention')
        
        data = {
            "name": "Charlie",
            "parent_contact_info": "987654321",
            "tag_ids": [tag.id]
        }
        
        response = self.client.post('/api/students/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        student = Student.objects.get(id=response.data['id'])
        self.assertEqual(student.tags.count(), 1)
        self.assertEqual(student.tags.first().item_value, 'Needs Attention')

    def test_update_teacher_without_password(self):
        """
        Ensure updating a teacher's info without providing a password succeeds.
        """
        teacher_user = User.objects.create_user(username='teacher_to_update', password='oldpassword')
        teacher = Teacher.objects.create(user=teacher_user, name='Old Name')

        data = {
            "name": "New Name"
            # No password or username is provided in the update payload
        }
        
        response = self.client.patch(f'/api/teachers/{teacher.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'New Name')

        # Verify the password has not been changed
        teacher_user.refresh_from_db()
        self.assertTrue(teacher_user.check_password('oldpassword'))


class V3_CourseOfferingApiTest(V2_BaseTestCase):
    def setUp(self):
        super().setUp()
        self.teacher_user = User.objects.create_user(username='offeringteacher', password='password')
        self.teacher = Teacher.objects.create(user=self.teacher_user)

    def test_create_course_offering(self):
        data = {
            "name": "2025 Fall Semester",
            "start_date": "2025-09-01",
            "end_date": "2026-01-15",
            "course_product_id": self.product1.id
        }
        response = self.client.post('/api/course-offerings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CourseOffering.objects.count(), 2)

    def test_enrollment_link_to_offering(self):
        offering = CourseOffering.objects.create(
            name="Summer Camp",
            start_date="2025-07-01",
            end_date="2025-08-31",
            course_product=self.product1
        )
        data = {
            "student_id": self.student1.id,
            "course_offering_id": offering.id,
            "total_lessons": 30
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        enrollment = Enrollment.objects.get(id=response.data['id'])
        self.assertEqual(enrollment.course_offering.id, offering.id)

    def test_schedule_date_validation(self):
        offering = CourseOffering.objects.create(
            name="Limited Time Offer",
            start_date="2025-10-01",
            end_date="2025-10-31",
            course_product=self.product1
        )
        enrollment = Enrollment.objects.create(
            student=self.student1, course_offering=offering,
            total_lessons=10
        )
        
        # This date is outside the offering's range
        invalid_start_time = timezone.make_aware(datetime.datetime(2025, 11, 1, 10, 0))
        invalid_end_time = invalid_start_time + datetime.timedelta(hours=1)

        data = {
            "enrollment_ids": [enrollment.id],
            "teacher_id": self.teacher.id,
            "classroom": self.classroom1.id,
            "start_time": invalid_start_time.isoformat(),
            "end_time": invalid_end_time.isoformat(),
        }
        response = self.client.post('/api/schedule-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_time', response.data)

    def test_cannot_update_active_offering(self):
        offering = CourseOffering.objects.create(
            name="Active Offering",
            start_date="2025-07-01",
            end_date="2025-08-31",
            course_product=self.product1,
            status='open' # Not in 'planning' status
        )
        data = {"name": "Updated Name"}
        response = self.client.patch(f'/api/course-offerings/{offering.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class V2_BatchScheduleApiTest(V2_BaseTestCase):
    def setUp(self):
        super().setUp()
        self.teacher_user = User.objects.create_user(username='batchteacher', password='password')
        self.teacher = Teacher.objects.create(user=self.teacher_user)
        self.student3 = Student.objects.create(name='Carol')
        self.enrollment3 = Enrollment.objects.create(
            student=self.student3, course_offering=self.offering1,
            total_lessons=10
        )

    def test_batch_create_success(self):
        data = {
            "enrollment_ids": [self.enrollment1.id, self.enrollment2.id],
            "teacher_id": self.teacher.id,
            "classroom": self.classroom1.id,
            "start_date": "2025-09-01", # Monday
            "end_date": "2025-09-10",
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "days_of_week": [0, 2, 4] # Mon, Wed, Fri
        }
        response = self.client.post('/api/schedule-entries/batch-create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Mon (1st), Wed (3rd), Fri (5th), Mon (8th), Wed (10th) = 5 entries
        self.assertEqual(len(response.data), 5)
        self.assertEqual(ScheduleEntry.objects.count(), 5)

    def test_batch_create_with_conflict(self):
        # Pre-create a conflicting entry on Wednesday
        conflicting_start = timezone.make_aware(datetime.datetime(2025, 9, 3, 10, 30))
        conflicting_end = conflicting_start + datetime.timedelta(hours=1)
        ScheduleEntry.objects.create(
            teacher_id=self.teacher.id,
            teacher_name=self.teacher.user.username,
            classroom=self.classroom1,
            start_time=conflicting_start,
            end_time=conflicting_end
        )

        data = {
            "enrollment_ids": [self.enrollment1.id],
            "teacher_id": self.teacher.id,
            "classroom": self.classroom1.id,
            "start_date": "2025-09-01",
            "end_date": "2025-09-10",
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "days_of_week": [0, 2, 4] # Mon, Wed, Fri
        }
        response = self.client.post('/api/schedule-entries/batch-create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
        self.assertIn('Teacher conflict on 2025-09-03', response.data['details'])
        # Ensure no entries were created due to the transaction
        self.assertEqual(ScheduleEntry.objects.count(), 1) # Only the manually created one


class DashboardStatsAPITest(V2_BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create users for each role
        self.teacher_user = User.objects.create_user(username='testteacher', password='password')
        self.teacher = Teacher.objects.create(user=self.teacher_user, name='Dr. Smith')

        self.student_user = User.objects.create_user(username='teststudent', password='password')
        self.student1.user = self.student_user
        self.student1.save()

        # Create some schedule entries for testing
        self.entry1 = ScheduleEntry.objects.create(
            teacher_id=self.teacher.id,
            teacher_name=self.teacher.name,
            classroom=self.classroom1,
            start_time=timezone.make_aware(datetime.datetime(2025, 9, 2, 10, 0)), # Tue
            end_time=timezone.make_aware(datetime.datetime(2025, 9, 2, 11, 0)), # 1 hour
            status='completed',
            course_name='Math G1',
            subject_name='Math'
        )
        self.entry1.students.add(self.student1)

        self.entry2 = ScheduleEntry.objects.create(
            teacher_id=self.teacher.id,
            teacher_name=self.teacher.name,
            classroom=self.classroom1,
            start_time=timezone.make_aware(datetime.datetime(2025, 9, 4, 14, 0)), # Thu
            end_time=timezone.make_aware(datetime.datetime(2025, 9, 4, 16, 0)), # 2 hours
            status='scheduled',
            course_name='Math G1',
            subject_name='Math'
        )
        self.entry2.students.add(self.student1, self.student2)

    def test_admin_stats(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/dashboard/stats/?start_date=2025-09-01&end_date=2025-09-07')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'admin')
        
        stats = response.data['stats']
        # 1 (entry1) + 2 (entry2) = 3 hours
        self.assertEqual(stats['kpis']['total_scheduled_hours'], 3.0)
        self.assertEqual(stats['kpis']['active_teachers_count'], 1)
        # student1 in entry1, student1 & student2 in entry2
        self.assertEqual(stats['kpis']['student_attendance_count'], 3)
        self.assertEqual(stats['kpis']['completed_courses_count'], 1)
        self.assertEqual(len(stats['charts']['teacher_workload']), 1)
        self.assertEqual(stats['charts']['teacher_workload'][0]['teacher_name'], 'Dr. Smith')

    def test_teacher_stats(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get('/api/dashboard/stats/?start_date=2025-09-01&end_date=2025-09-07')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'teacher')

        stats = response.data['stats']
        self.assertEqual(stats['kpis']['total_hours'], 3.0)
        self.assertEqual(stats['kpis']['course_count'], 2)
        self.assertEqual(stats['kpis']['student_count'], 3)
        self.assertEqual(stats['charts']['subject_distribution'][0]['subject_name'], 'Math')

    def test_student_stats(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get('/api/dashboard/stats/?start_date=2025-09-01&end_date=2025-09-07')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'student')

        stats = response.data['stats']
        self.assertEqual(stats['kpis']['course_count'], 2)
        self.assertEqual(stats['kpis']['total_hours'], 3.0)
        # Assuming total_lessons=10, used_lessons=0 initially
        self.assertEqual(stats['kpis']['remaining_lessons'], 10)
