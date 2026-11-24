from celery import shared_task
from django.utils import timezone

from .models import Season
from .services import close_season


@shared_task
def close_due_seasons() -> int:
    due = Season.objects.filter(status=Season.Status.ACTIVE, ends_on__lt=timezone.localdate())
    for season in due:
        close_season(season)
    return len(due)
