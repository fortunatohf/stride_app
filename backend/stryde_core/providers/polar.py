"""Polar AccessLink API v3 (open developer registration). Webhook event -> download FIT for the exercise."""

from __future__ import annotations

from urllib.parse import urlencode

from ..track import Source
from .base import ActivityRef, FileProviderMixin, HttpGet, ProviderStatus


class PolarProvider(FileProviderMixin):
    key = "polar"
    name = "Polar"
    source = Source.POLAR
    status = ProviderStatus.NEEDS_KEYS
    AUTH_URL = "https://flow.polar.com/oauth2/authorization"

    def authorize_url(self, client_id: str, redirect_uri: str, state: str) -> str:
        return f"{self.AUTH_URL}?" + urlencode(
            {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri, "state": state}
        )

    def parse_webhook(self, payload: dict) -> list[ActivityRef]:
        if payload.get("event") != "EXERCISE" or not payload.get("url"):
            return []
        return [
            ActivityRef(
                provider=self.key,
                external_user_id=str(payload.get("user_id", "")),
                external_id=str(payload.get("entity_id", "")),
                file_url=payload["url"].rstrip("/") + "/fit",
                file_type="FIT",
            )
        ]

    def download(self, ref: ActivityRef, access_token: str | None, http: HttpGet) -> bytes:
        return http(ref.file_url, {"Authorization": f"Bearer {access_token}", "Accept": "*/*"})
