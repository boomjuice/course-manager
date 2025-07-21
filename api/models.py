from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class BaseModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_time` and `updated_time` fields, and user tracking as string names.
    """
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间", null=True)
    created_by = models.CharField(max_length=150, null=True, blank=True, verbose_name="创建人")
    updated_by = models.CharField(max_length=150, null=True, blank=True, verbose_name="最后修改人")

    class Meta:
        abstract = True


class DataDictionary(BaseModel):
    """
    Data Dictionary for storing grouped key-value pairs.
    e.g., group_code='grades', item_value='高一'
    """
    group_code = models.CharField(max_length=100, verbose_name="组代码")
    item_value = models.CharField(max_length=100, verbose_name="显示值")
    subgroup = models.CharField(max_length=100, blank=True, null=True, verbose_name="子分组")
    sort_order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        unique_together = ('group_code', 'item_value')
        ordering = ['group_code', 'sort_order', 'item_value']
        verbose_name = "数据字典"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"[{self.group_code}] {self.item_value}"


class CourseProduct(BaseModel):
    subject = models.CharField(max_length=100, verbose_name="科目")
    grade = models.CharField(max_length=100, verbose_name="年级")
    course_type = models.CharField(max_length=100, verbose_name="课程类型")
    duration_minutes = models.IntegerField(verbose_name="标准单节课时长(分钟)")

    @property
    def display_name(self):
        return f"{self.grade}{self.subject}({self.course_type})"

    def __str__(self):
        return self.display_name


class CourseOffering(BaseModel):
    STATUS_CHOICES = [
        ('planning', '计划中'),
        ('open', '报名中'),
        ('in_progress', '已开课'),
        ('completed', '已结束'),
    ]
    course_product = models.ForeignKey(CourseProduct, on_delete=models.PROTECT, verbose_name="课程产品")
    name = models.CharField(max_length=255, verbose_name="开班计划名称")
    start_date = models.DateField(verbose_name="开始日期")
    end_date = models.DateField(verbose_name="结束日期")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="状态")

    @property
    def display_name(self):
        return f"{self.name} - {self.course_product.display_name}"

    def get_enrolled_students(self):
        return Student.objects.filter(enrollment__course_offering=self).distinct()

    def __str__(self):
        return self.display_name


class Enrollment(BaseModel):
    student = models.ForeignKey('Student', on_delete=models.PROTECT, verbose_name="学生")
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.PROTECT, verbose_name="开班计划")
    total_lessons = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="总购买课时")
    used_lessons = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="已消耗课时")

    @property
    def display_name(self):
        return f"{self.course_offering.display_name} - {self.student.name}"

    def __str__(self):
        return self.display_name


class Campus(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="校区名称")
    address = models.CharField(max_length=255, blank=True, verbose_name="校区地址")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return self.name


class Classroom(BaseModel):
    name = models.CharField(max_length=100, verbose_name="教室名称/编号")
    capacity = models.PositiveIntegerField(verbose_name="容纳人数")
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, verbose_name="所属校区")
    is_active = models.BooleanField(default=True, verbose_name="是否可用")

    def __str__(self):
        return f'{self.campus.name} - {self.name}'


class Teacher(BaseModel):
    phone_regex = RegexValidator(
        regex=r'^1[3-9]\d{9}$',
        message="请输入有效的手机号码。"
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="关联用户")
    name = models.CharField(max_length=100, verbose_name="教师姓名")
    contact_info = models.CharField(validators=[phone_regex], max_length=20, verbose_name="联系方式")
    subjects = models.ManyToManyField(DataDictionary, related_name='teachers_by_subject',
                                      limit_choices_to={'group_code': 'subjects'}, verbose_name="可教科目")
    grades = models.ManyToManyField(DataDictionary, related_name='teachers_by_grade',
                                    limit_choices_to={'group_code': 'grades'}, verbose_name="可教年级")

    def __str__(self):
        return self.name


class Student(BaseModel):
    phone_regex = RegexValidator(
        regex=r'^1[3-9]\d{9}$',
        message="请输入有效的手机号码。"
    )
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联用户")
    name = models.CharField(max_length=100, verbose_name="学生姓名")
    school = models.CharField(max_length=100, blank=True, verbose_name="学校")
    grade = models.ForeignKey(
        DataDictionary, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="年级", limit_choices_to={'group_code': 'grades'},
        related_name='students_by_grade'
    )
    parent_contact_info = models.CharField(validators=[phone_regex], max_length=100, verbose_name="家长联系方式", default='19900000000')
    tags = models.ManyToManyField(
        DataDictionary, verbose_name="学生标签", blank=True,
        limit_choices_to={'group_code': 'student_tags'},
        related_name='students_by_tag'
    )
    notes = models.TextField(blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否在读")

    def __str__(self):
        return self.name


class ScheduleEntry(BaseModel):
    STATUS_CHOICES = [
        ('scheduled', '已安排'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    start_time = models.DateTimeField(verbose_name="课程开始时间")
    end_time = models.DateTimeField(verbose_name="课程结束时间")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="课程状态")
    lessons_consumed = models.DecimalField(max_digits=10, decimal_places=2, default=1.0,
                                           verbose_name="本节课消耗课时数")

    # Snapshot fields
    teacher_id = models.IntegerField(null=True, blank=True, verbose_name="教师ID快照")
    teacher_name = models.CharField(max_length=150, verbose_name="教师姓名", default='')
    classroom_name = models.CharField(max_length=100, verbose_name="教室名称", default='')
    course_name = models.CharField(max_length=255, verbose_name="课程名称", default='')
    subject_name = models.CharField(max_length=100, verbose_name="科目名称", default='')
    grade_name = models.CharField(max_length=100, verbose_name="年级名称", default='')

    # Relationships
    students = models.ManyToManyField('Student', verbose_name="参与学生", blank=True)
    enrollments = models.ManyToManyField(Enrollment, verbose_name="关联报名", blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, null=True, blank=True, verbose_name="使用教室")
    notes = models.TextField(blank=True, verbose_name="课程备注")

    def __str__(self):
        return f'{self.course_name} @ {self.start_time.strftime("%Y-%m-%d %H:%M")}'


class Attendance(BaseModel):
    STATUS_CHOICES = [
        ('present', '出勤'),
        ('absent', '缺勤'),
        ('leave', '请假'),
    ]
    schedule_entry = models.ForeignKey('ScheduleEntry', on_delete=models.CASCADE, verbose_name="课表条目")
    student = models.ForeignKey('Student', on_delete=models.CASCADE, verbose_name="学生")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present', verbose_name="考勤状态")

    class Meta:
        unique_together = ('schedule_entry', 'student')
        verbose_name = "考勤记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.student.name} - {self.schedule_entry} - {self.get_status_display()}"