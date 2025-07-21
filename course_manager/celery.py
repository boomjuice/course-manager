# course_manager/celery.py
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_manager.settings')

app = Celery('course_manager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'mark-completed-schedules-every-hour': {
        'task': 'api.tasks.mark_completed_schedules',
        'schedule': crontab(minute=0, hour='*'), # Runs at the start of every hour
    },
    'update-offering-statuses-daily': {
        'task': 'api.tasks.update_offering_statuses',
        'schedule': crontab(minute=0, hour=0), # Runs daily at midnight
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')