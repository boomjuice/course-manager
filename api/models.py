from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BaseModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_time` and `updated_time` fields, and user tracking as string names.
    """
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    created_by = models.CharField(max_length=150, null=True, blank=True, verbose_name="创建人")
    updated_by = models.CharField(max_length=150, null=True, blank=True, verbose_name="最后修改人")

    class Meta:
        abstract = True

class Campus(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="校区名称")
    address = models.CharField(max_length=255, blank=True, verbose_name="校区地址")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    def __str__(self):
        return self.name

class Subject(BaseModel):
    name = models.CharField(max_length=50, unique=True, verbose_name="科目名称")

    def __str__(self):
        return self.name

class Grade(BaseModel):
    name = models.CharField(max_length=50, unique=True, verbose_name="年级名称")

    def __str__(self):
        return self.name

class Tag(BaseModel):
    TAG_GROUP_CHOICES = [
        ('performance', '成绩表现'),
        ('school_info', '学校信息'),
        ('personality', '性格特点'),
        ('source', '来源渠道'),
        ('other', '其他'),
    ]
    name = models.CharField(max_length=50, unique=True, verbose_name="标签名称")
    group = models.CharField(
        max_length=20,
        choices=TAG_GROUP_CHOICES,
        default='other',
        verbose_name="标签组别"
    )

    def __str__(self):
        return f'[{self.get_group_display()}] {self.name}'

class Classroom(BaseModel):
    name = models.CharField(max_length=100, verbose_name="教室名称/编号")
    capacity = models.PositiveIntegerField(verbose_name="容纳人数")
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, verbose_name="所属校区")
    is_active = models.BooleanField(default=True, verbose_name="是否可用")

    def __str__(self):
        return f'{self.campus.name} - {self.name}'

class TimeSlot(BaseModel):
    template_name = models.CharField(max_length=100, verbose_name="模板名称")
    start_time = models.TimeField(verbose_name="开始时间")
    end_time = models.TimeField(verbose_name="结束时间")

    def __str__(self):
        return f'{self.template_name} ({self.start_time.strftime("%H:%M")} - {self.end_time.strftime("%H:%M")})'

class Teacher(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="关联用户")
    contact_info = models.CharField(max_length=100, blank=True, verbose_name="联系方式")
    subjects = models.ManyToManyField(Subject, verbose_name="可教科目", blank=True)
    grades = models.ManyToManyField(Grade, verbose_name="可教年级", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="是否在职")

    def __str__(self):
        return self.user.username

class Student(BaseModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联用户")
    name = models.CharField(max_length=100, verbose_name="学生姓名")
    parent_contact_info = models.CharField(max_length=100, blank=True, verbose_name="家长联系方式")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="学生标签")
    is_active = models.BooleanField(default=True, verbose_name="是否在读")

    def __str__(self):
        return self.name

class TeachingClass(BaseModel):
    CLASS_TYPE_CHOICES = [
        ('small_group', '小班'),
        ('one_on_one', '一对一'),
    ]
    name = models.CharField(max_length=100, verbose_name="班级名称")
    class_type = models.CharField(max_length=20, choices=CLASS_TYPE_CHOICES, verbose_name="班级类型")
    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, verbose_name="授课教师")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, verbose_name="所授科目")
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, verbose_name="所属年级")
    students = models.ManyToManyField(Student, verbose_name="班内学���", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="班级是否有效")

    def __str__(self):
        return self.name

class ScheduleEntry(BaseModel):
    STATUS_CHOICES = [
        ('scheduled', '已安排'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, verbose_name="所属教学班")
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, verbose_name="使用教室")
    start_time = models.DateTimeField(verbose_name="课程开始时间")
    end_time = models.DateTimeField(verbose_name="课程结束时间")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="课程状态")

    def __str__(self):
        return f'{self.teaching_class.name} @ {self.start_time.strftime("%Y-%m-%d %H:%M")}'