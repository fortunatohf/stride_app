from celery import shared_task

from .models import Activity
from .services import process_activity


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_activity_task(self, activity_id: int) -> int:
    activity = Activity.objects.select_related("user").get(pk=activity_id)
    try:
        return len(process_activity(activity))
    except Exception as exc:  # keep the error on the activity for support, then retry
        Activity.objects.filter(pk=activity_id).update(state=Activity.State.FAILED, error=str(exc)[:500])
        raise self.retry(exc=exc)
