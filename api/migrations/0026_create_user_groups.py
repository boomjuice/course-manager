# Generated by Django 4.2.23 on 2025-07-21 15:16

from django.db import migrations

def create_user_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='teacher_group')
    Group.objects.get_or_create(name='student_group')

def remove_user_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['teacher_group', 'student_group']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_teacher_contact_info_and_more'),
    ]

    operations = [
        migrations.RunPython(create_user_groups, remove_user_groups),
    ]
