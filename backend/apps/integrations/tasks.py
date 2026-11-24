from celery import shared_task

from .models import WebhookEvent
from .services import process_webhook


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def process_webhook_task(self, event_id: int) -> int:
    event = WebhookEvent.objects.get(pk=event_id)
    try:
        return process_webhook(event)
    except Exception as exc:
        raise self.retry(exc=exc)
