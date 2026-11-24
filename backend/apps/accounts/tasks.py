from celery import shared_task

from .push import send_push


@shared_task
def send_push_task(user_id: int, title: str, body: str, data: dict | None = None) -> int:
    return send_push(user_id, title, body, data)
