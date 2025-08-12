from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from .models import Task

@shared_task
def send_task_reminder(task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return {"status": "not_found", "task_id": task_id}

    if task.is_deleted or task.status == Task.STATUS_COMPLETED:
        return {"status": "skipped", "reason": "deleted_or_completed"}

    subject = f"Reminder: '{task.title}' due at {task.due_date}"
    body = f"Hello {task.assigned_user.username},\n\nThis is a reminder that your task '{task.title}' (product: {task.product.name}) is due at {task.due_date}.\n\nDescription: {task.description}\n\nRegards."
    recipient = [task.assigned_user.email] if task.assigned_user.email else []
    if recipient:
        send_mail(subject, body, None, recipient, fail_silently=False)
        return {"status": "sent", "task_id": task_id}
    return {"status": "no_email", "task_id": task_id}


@shared_task
def schedule_reminders():
    """
    Run periodically (via Celery Beat). Find tasks due ~1 hour from now and schedule send_task_reminder.
    We look for tasks due between now+59 and now+61 minutes to account for schedule frequency.
    """
    now = timezone.now()
    window_start = now + timedelta(minutes=59)
    window_end = now + timedelta(minutes=61)
    qs = Task.objects.filter(is_deleted=False, status__in=[Task.STATUS_PENDING, Task.STATUS_INPROGRESS],
                             due_date__gte=window_start, due_date__lte=window_end)
    for t in qs:
        send_task_reminder.delay(t.id)
    return {"scheduled": qs.count()}
