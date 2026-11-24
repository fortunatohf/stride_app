"""Comeback plan: one week of training aimed at taking a specific route back.

Rule-based on purpose. The week template should be reviewed and signed off by a certified coach before launch.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction

from .models import TrainingPlan, TrainingSession

WEEK = [  # (day offset, kind, title, minutes)
    (0, "rest", "Rest + mobility", None),
    (1, "easy", "Easy run", 35),
    (2, "tempo", "Tempo 3 x 8 min", 45),
    (3, "rest", "Rest", None),
    (4, "easy", "Easy run", 30),
    (5, "shakeout", "Shakeout", 20),
    (6, "attempt", "Win back {route}", None),
]


def _pace(seconds_per_km: float) -> str:
    m, s = divmod(int(round(seconds_per_km)), 60)
    return f"{m}:{s:02d}/km"


def target_time(user, route) -> float:
    """Aim 5 s under the current record (a tie keeps the champion, so the goal must be strictly faster)."""
    return float(int(route.record_s) - 5)


@transaction.atomic
def create_comeback_plan(user, route, today: date | None = None) -> TrainingPlan:
    today = today or date.today()
    TrainingPlan.objects.filter(user=user, active=True, kind=TrainingPlan.Kind.COMEBACK).update(active=False)
    goal = target_time(user, route)
    goal_pace = goal / (route.distance_m / 1000)
    plan = TrainingPlan.objects.create(
        user=user,
        kind=TrainingPlan.Kind.COMEBACK,
        title=f"Take back {route.name}",
        route=route,
        goal_time_s=goal,
        starts_on=today,
        attempt_on=today + timedelta(days=6),
    )
    details = {
        "rest": "Recovery",
        "easy": "Conversational pace",
        "tempo": f"Hold about {_pace(goal_pace + 5)} for each 8 min block, 2 min easy between",
        "shakeout": "Light legs, 4 short strides",
        "attempt": f"Target under {int(goal // 60)}:{int(goal % 60):02d}",
    }
    TrainingSession.objects.bulk_create(
        [
            TrainingSession(
                plan=plan, date=today + timedelta(days=d), kind=k, title=t.format(route=route.name), detail=details[k], minutes=m
            )
            for d, k, t, m in WEEK
        ]
    )
    return plan
