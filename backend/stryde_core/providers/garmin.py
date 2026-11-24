"""Garmin Connect Developer Program — Activity API (push of activity files).

Flow:
1. User taps "Connect Garmin" -> we redirect to Garmin's consent page (OAuth).
2. After each synced workout Garmin POSTs to our webhook with one or more activity-file notices.
3. We download the FIT from the notice's callback URL and import it.

Field names follow Garmin's Activity API push notifications. Re-check them against the docs you get after
approval and update `parse_webhook` + tests if anything differs.
"""

from __future__ import annotations

from urllib.parse import urlencode

from ..track import Source
from .base import ActivityRef, FileProviderMixin, HttpGet, ProviderStatus


class GarminProvider(FileProviderMixin):
    key = "garmin"
    name = "Garmin"
    source = Source.GARMIN
    status = ProviderStatus.NEEDS_KEYS
    AUTH_URL = "https://connect.garmin.com/oauth2Confirm"

    def authorize_url(self, client_id: str, redirect_uri: str, state: str) -> str:
        return f"{self.AUTH_URL}?" + urlencode(
            {"client_id": client_id, "response_type": "code", "redirect_uri": redirect_uri, "state": state}
        )

    def parse_webhook(self, payload: dict) -> list[ActivityRef]:
        refs = []
        for item in payload.get("activityFiles", []):
            if not item.get("callbackURL"):
                continue
            refs.append(
                ActivityRef(
                    provider=self.key,
                    external_user_id=str(item.get("userId", "")),
                    external_id=str(item.get("summaryId") or item.get("activityId") or ""),
                    file_url=item["callbackURL"],
                    file_type=str(item.get("fileType", "FIT")).upper(),
                    manual=bool(item.get("manual", False)),
                    extra={"start": item.get("startTimeInSeconds"), "activity_type": item.get("activityType")},
                )
            )
        return refs

    def download(self, ref: ActivityRef, access_token: str | None, http: HttpGet) -> bytes:
        headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
        return http(ref.file_url, headers)
