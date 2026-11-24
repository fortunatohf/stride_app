"""Suunto — partner API (application required). Scaffold: workouts are downloadable as FIT."""

from __future__ import annotations

from ..track import Source
from .base import ActivityRef, FileProviderMixin, HttpGet, ProviderStatus


class SuuntoProvider(FileProviderMixin):
    key = "suunto"
    name = "Suunto"
    source = Source.SUUNTO
    status = ProviderStatus.SCAFFOLD

    def authorize_url(self, client_id: str, redirect_uri: str, state: str) -> str:
        raise NotImplementedError("Add the Suunto OAuth URL from the partner docs")

    def parse_webhook(self, payload: dict) -> list[ActivityRef]:
        # TODO(partner docs): confirm event type and field names for new workouts.
        if payload.get("type") != "WORKOUT_CREATED":
            return []
        wid = str(payload.get("workoutid") or payload.get("workoutKey") or "")
        return [
            ActivityRef(
                self.key, str(payload.get("username", "")), wid, f"https://cloudapi.suunto.com/v2/workout/exportFit/{wid}"
            )
        ]

    def download(self, ref: ActivityRef, access_token: str | None, http: HttpGet) -> bytes:
        return http(ref.file_url, {"Authorization": f"Bearer {access_token}"})
