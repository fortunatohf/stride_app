from rest_framework.response import Response
from rest_framework.views import APIView

from .services import POINTS, WEEKLY_CAP, active_season, membership_for, standings


class CurrentLeagueView(APIView):
    def get(self, request):
        season = active_season(request.user.city)
        if not season:
            return Response({"season": None})
        me = membership_for(request.user, season)
        rows = standings(me.division)
        return Response(
            {
                "season": {
                    "city": season.city,
                    "number": season.number,
                    "starts_on": season.starts_on,
                    "ends_on": season.ends_on,
                },
                "tier": me.division.tier,
                "weekly_cap": WEEKLY_CAP,
                "points_table": {k: v[0] for k, v in POINTS.items() if v[0]},
                "standings": [
                    {
                        "rank": i + 1,
                        "user_id": m.user_id,
                        "name": m.user.public_name,
                        "points": m.points,
                        "me": m.user_id == request.user.id,
                    }
                    for i, m in enumerate(rows)
                ],
            }
        )
