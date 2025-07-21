from celery import shared_task
from django.utils import timezone
from .models import ScheduleEntry, CourseOffering

@shared_task
def mark_completed_schedules():
    now = timezone.now()
    ScheduleEntry.objects.filter(end_time__lt=now, status='scheduled').update(status='completed')

@shared_task
def update_offering_statuses():
    today = timezone.now().date()
    
    # Mark open offerings as in_progress if start_date has passed
    CourseOffering.objects.filter(
        status='open',
        start_date__lte=today
    ).update(status='in_progress')

    # Mark in_progress offerings as completed if end_date has passed
    CourseOffering.objects.filter(
        status='in_progress',
        end_date__lt=today
    ).update(status='completed')

