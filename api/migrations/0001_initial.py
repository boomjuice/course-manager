# Generated by Django 5.1.11 on 2025-07-19 04:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Campus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(max_length=100)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('capacity', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('campus', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.campus')),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent_contact_info', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, to='api.tag')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_info', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('grades', models.ManyToManyField(to='api.grade')),
                ('subjects', models.ManyToManyField(to='api.subject')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TeachingClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('class_type', models.CharField(choices=[('small_group', '小班'), ('one_on_one', '一对一')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('grade', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.grade')),
                ('students', models.ManyToManyField(to='api.student')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.teacher')),
            ],
        ),
        migrations.CreateModel(
            name='ScheduleEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('scheduled', '已安排'), ('completed', '已完成'), ('cancelled', '已取消')], default='scheduled', max_length=20)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.classroom')),
                ('teaching_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.teachingclass')),
            ],
        ),
    ]
