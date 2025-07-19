import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from api.models import (
    Campus, Subject, Grade, Tag, Classroom, TimeSlot,
    Teacher, Student, TeachingClass, ScheduleEntry
)

class Command(BaseCommand):
    help = 'Creates a rich set of test data for the application.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Deleting old data...')
        # 清理旧数据，注意顺序，避免外键约束问题
        ScheduleEntry.objects.all().delete()
        TeachingClass.objects.all().delete()
        Teacher.objects.all().delete()
        Student.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Group.objects.all().delete()
        TimeSlot.objects.all().delete()
        Classroom.objects.all().delete()
        Campus.objects.all().delete()
        Subject.objects.all().delete()
        Grade.objects.all().delete()
        Tag.objects.all().delete()

        self.stdout.write('Creating new test data...')

        # --- 基础数据 ---
        campus = Campus.objects.create(name='总部校区', address='城市中心路123号')
        
        subjects = {
            'math': Subject.objects.create(name='数学'),
            'english': Subject.objects.create(name='英语'),
            'physics': Subject.objects.create(name='物理')
        }
        
        grades = {
            'g10': Grade.objects.create(name='高一'),
            'g11': Grade.objects.create(name='高二'),
            'g12': Grade.objects.create(name='高三')
        }

        tags = [
            Tag.objects.create(name='基础薄弱'),
            Tag.objects.create(name='冲刺拔高'),
            Tag.objects.create(name='来自A校'),
            Tag.objects.create(name='需要督促')
        ]

        Classroom.objects.create(name='101教室', capacity=20, campus=campus)
        Classroom.objects.create(name='VIP单间', capacity=1, campus=campus)

        TimeSlot.objects.create(template_name='上午第一节', start_time='08:00:00', end_time='09:30:00')
        TimeSlot.objects.create(template_name='上午第二节', start_time='10:00:00', end_time='11:30:00')
        TimeSlot.objects.create(template_name='下午第一节', start_time='14:00:00', end_time='15:30:00')

        # --- 角色和用户 ---
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group, _ = Group.objects.get_or_create(name='Student')

        # 创建张老师
        teacher_user_zhang, _ = User.objects.get_or_create(username='zhanglaoshi', first_name='三', last_name='张')
        teacher_user_zhang.set_password('password')
        teacher_user_zhang.save()
        teacher_user_zhang.groups.add(teacher_group)
        teacher_zhang = Teacher.objects.create(user=teacher_user_zhang, contact_info='13800138001')
        teacher_zhang.subjects.add(subjects['math'], subjects['physics'])
        teacher_zhang.grades.add(grades['g10'], grades['g11'])

        # 创建李老师
        teacher_user_li, _ = User.objects.get_or_create(username='lilaoshi', first_name='四', last_name='李')
        teacher_user_li.set_password('password')
        teacher_user_li.save()
        teacher_user_li.groups.add(teacher_group)
        teacher_li = Teacher.objects.create(user=teacher_user_li, contact_info='13800138002')
        teacher_li.subjects.add(subjects['english'])
        teacher_li.grades.add(grades['g11'], grades['g12'])

        # 创建学生
        student_names = ['小明', '小红', '小刚', '小丽', '小华']
        students = []
        for i, name in enumerate(student_names):
            student_user, _ = User.objects.get_or_create(username=f'student{i+1}')
            student_user.set_password('password')
            student_user.save()
            student_user.groups.add(student_group)
            student = Student.objects.create(user=student_user, name=name, parent_contact_info=f'1390013900{i}')
            # 随机分配1-2个标签
            student.tags.add(*random.sample(tags, k=random.randint(1, 2)))
            students.append(student)

        # --- 教学班 ---
        # 张老师的高一数学小班
        math_class = TeachingClass.objects.create(
            name='高一数学暑期班',
            class_type='small_group',
            teacher=teacher_zhang,
            subject=subjects['math'],
            grade=grades['g10']
        )
        math_class.students.add(students[0], students[1], students[2]) # 小明、小红、小刚

        # 李老师的高二英语一对一
        english_class = TeachingClass.objects.create(
            name='高二英语1对1',
            class_type='one_on_one',
            teacher=teacher_li,
            subject=subjects['english'],
            grade=grades['g11']
        )
        english_class.students.add(students[3]) # 小丽

        self.stdout.write(self.style.SUCCESS(f'Successfully created test data for {Teacher.objects.count()} teachers and {Student.objects.count()} students.'))