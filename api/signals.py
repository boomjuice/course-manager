from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import ScheduleEntry, Attendance, Enrollment

@receiver(post_save, sender=ScheduleEntry)
def deduct_lessons_on_completion(sender, instance, created, **kwargs):
    """
    When a ScheduleEntry's status is changed to 'completed', deduct lessons
    from the corresponding enrollments for students who were present.
    """
    if instance.status == 'completed' and not created:
        # We only want to trigger this when the status is updated to completed.
        
        # Get all "present" attendances for this schedule entry
        present_attendances = Attendance.objects.filter(
            schedule_entry=instance,
            status='present'
        )
        
        for attendance in present_attendances:
            student = attendance.student
            # Find the relevant enrollment for this student and course
            try:
                enrollment = instance.enrollments.get(student=student)
                
                # Calculate lesson consumption
                duration_minutes = (instance.end_time - instance.start_time).total_seconds() / 60
                standard_duration = enrollment.course_offering.course_product.duration_minutes
                
                if standard_duration > 0:
                    lessons_consumed = duration_minutes / standard_duration
                else:
                    lessons_consumed = 0 # Avoid division by zero
                
                # Deduct lessons
                Enrollment.objects.filter(id=enrollment.id).update(
                    used_lessons=models.F('used_lessons') + lessons_consumed
                )

            except Enrollment.DoesNotExist:
                # Handle case where student is in schedule but has no matching enrollment
                # This might be a data integrity issue or a specific business logic case
                pass

@receiver(post_delete)
def delete_user_on_profile_delete(sender, instance, **kwargs):
    # This signal is generic and will be connected specifically in apps.py
    if hasattr(instance, 'user') and instance.user:
        instance.user.delete()
