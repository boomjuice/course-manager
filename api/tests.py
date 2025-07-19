from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Campus, Subject, Grade, Classroom, Teacher, Student, TeachingClass, ScheduleEntry, TimeSlot
import datetime
from django.utils import timezone

class AuthAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_success(self):
        """
        Ensure a user can log in with correct credentials and receive a token.
        """
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_failure(self):
        """
        Ensure a user cannot log in with incorrect credentials.
        """
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)


class ScheduleConflictTest(APITestCase):
    def setUp(self):
        # Setup a user with staff permissions and authenticate
        self.admin_user = User.objects.create_user(username='admin', password='password', is_staff=True)
        self.client.force_authenticate(user=self.admin_user)

        # Basic data
        self.campus = Campus.objects.create(name='Main Campus')
        self.subject = Subject.objects.create(name='Math')
        self.grade = Grade.objects.create(name='Grade 10')
        self.classroom1 = Classroom.objects.create(name='Room 101', capacity=30, campus=self.campus)
        self.classroom2 = Classroom.objects.create(name='Room 102', capacity=30, campus=self.campus)

        # Teachers
        self.teacher1_user = User.objects.create_user(username='teacher1', password='password')
        self.teacher1 = Teacher.objects.create(user=self.teacher1_user)
        self.teacher2_user = User.objects.create_user(username='teacher2', password='password')
        self.teacher2 = Teacher.objects.create(user=self.teacher2_user)

        # Students
        self.student1 = Student.objects.create(name='John Doe')

        # Teaching class
        self.class1 = TeachingClass.objects.create(
            name='Math Class A', teacher=self.teacher1, subject=self.subject, grade=self.grade
        )
        self.class1.students.add(self.student1)

        # Existing schedule entry
        self.start_time = timezone.make_aware(datetime.datetime(2025, 7, 21, 10, 0, 0))
        self.end_time = timezone.make_aware(datetime.datetime(2025, 7, 21, 11, 30, 0))
        
        ScheduleEntry.objects.create(
            teaching_class=self.class1, classroom=self.classroom1, start_time=self.start_time, end_time=self.end_time
        )

    def test_classroom_conflict(self):
        """
        Test that creating a schedule entry in a classroom that is already booked fails.
        """
        conflicting_class = TeachingClass.objects.create(
            name='Science Class', teacher=self.teacher2, subject=self.subject, grade=self.grade
        )
        data = {
            'teaching_class': conflicting_class.id,
            'classroom': self.classroom1.id, # Using the same classroom
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }
        response = self.client.post('/api/schedule-entries/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('classroom', response.data)

    def test_teacher_conflict(self):
        """
        Test that creating a schedule entry for a teacher who is already booked fails.
        """
        conflicting_class = TeachingClass.objects.create(
            name='History Class', teacher=self.teacher1, subject=self.subject, grade=self.grade # Using the same teacher
        )
        data = {
            'teaching_class': conflicting_class.id,
            'classroom': self.classroom2.id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }
        response = self.client.post('/api/schedule-entries/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('teacher', response.data)

    def test_student_conflict(self):
        """
        Test that creating a schedule entry for a class with a student who is already booked fails.
        """
        conflicting_class = TeachingClass.objects.create(
            name='Art Class', teacher=self.teacher2, subject=self.subject, grade=self.grade
        )
        conflicting_class.students.add(self.student1) # Using the same student
        data = {
            'teaching_class': conflicting_class.id,
            'classroom': self.classroom2.id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }
        response = self.client.post('/api/schedule-entries/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('student_conflict', response.data)


class ScheduleIntegrationTest(APITestCase):
    def setUp(self):
        # Admin user for making API calls
        self.admin_user = User.objects.create_user(username='admin', password='password', is_staff=True)
        self.client.force_authenticate(user=self.admin_user)

        # Core data
        self.campus = Campus.objects.create(name='Main Campus')
        self.subject_math = Subject.objects.create(name='Math')
        self.subject_sci = Subject.objects.create(name='Science')
        self.grade = Grade.objects.create(name='Grade 10')
        self.classroom = Classroom.objects.create(name='Room 101', capacity=30, campus=self.campus)
        self.timeslot = TimeSlot.objects.create(template_name='Morning Slot', start_time='09:00:00', end_time='10:30:00')

        # Teacher 1 and their class
        teacher1_user = User.objects.create_user(username='teacher1', password='password')
        self.teacher1 = Teacher.objects.create(user=teacher1_user)
        self.student1 = Student.objects.create(name='Alice')
        self.class1 = TeachingClass.objects.create(
            name='Math Class A', teacher=self.teacher1, subject=self.subject_math, grade=self.grade
        )
        self.class1.students.add(self.student1)

        # Teacher 2 and their class
        teacher2_user = User.objects.create_user(username='teacher2', password='password')
        self.teacher2 = Teacher.objects.create(user=teacher2_user)
        self.student2 = Student.objects.create(name='Bob')
        self.class2 = TeachingClass.objects.create(
            name='Science Class B', teacher=self.teacher2, subject=self.subject_sci, grade=self.grade
        )
        self.class2.students.add(self.student2)

    def test_batch_create_and_filter_flow(self):
        """
        An integration test for the full flow:
        1. Batch create schedule entries for two different classes.
        2. Verify the creation.
        3. Filter the results by teacher, student, and subject.
        """
        # Step 1: Batch create for the first class (Math with Teacher1)
        batch_data1 = {
            'teaching_class_id': self.class1.id,
            'classroom_id': self.classroom.id,
            'timeslot_id': self.timeslot.id,
            'start_date': '2025-08-04',  # A Monday
            'end_date': '2025-08-10',
            'days_of_week': [0, 2]  # Monday, Wednesday
        }
        response1 = self.client.post('/api/schedule-entries/batch-create/', batch_data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data['created_count'], 2) # Mon, Wed

        # Step 2: Batch create for the second class (Science with Teacher2)
        batch_data2 = {
            'teaching_class_id': self.class2.id,
            'classroom_id': self.classroom.id,
            'timeslot_id': self.timeslot.id,
            'start_date': '2025-08-04',
            'end_date': '2025-08-10',
            'days_of_week': [1, 3]  # Tuesday, Thursday
        }
        response2 = self.client.post('/api/schedule-entries/batch-create/', batch_data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data['created_count'], 2) # Tue, Thu

        # Verify total entries
        self.assertEqual(ScheduleEntry.objects.count(), 4)

        # Step 3: Test filtering
        # Filter by Teacher 1
        response_t1 = self.client.get(f'/api/schedule-entries/?teacher={self.teacher1.id}')
        self.assertEqual(response_t1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_t1.data['results']), 2)
        self.assertEqual(response_t1.data['results'][0]['teaching_class']['name'], 'Math Class A')

        # Filter by Student 2
        response_s2 = self.client.get(f'/api/schedule-entries/?student={self.student2.id}')
        self.assertEqual(response_s2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_s2.data['results']), 2)
        self.assertEqual(response_s2.data['results'][0]['teaching_class']['name'], 'Science Class B')

        # Filter by Subject (Science)
        response_subj = self.client.get(f'/api/schedule-entries/?subject={self.subject_sci.id}')
        self.assertEqual(response_subj.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_subj.data['results']), 2)

        # Filter by a date range that only includes the Tuesday and Wednesday classes
        response_date = self.client.get('/api/schedule-entries/?start_date=2025-08-05&end_date=2025-08-06')
        self.assertEqual(response_date.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_date.data['results']), 2)