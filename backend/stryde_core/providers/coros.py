"""COROS — partner API (application required). Scaffold: fill in URLs and payload fields from the
partner documentation once approved. Activities arrive as FIT files, so `to_track` already works."""

from __future__ import annotations

from ..track import Source
from .base import ActivityRef, FileProviderMixin, HttpGet, ProviderStatus


class CorosProvider(FileProviderMixin):
    key = "coros"
    name = "COROS"
    source = Source.COROS
    status = ProviderStatus.SCAFFOLD

    def authorize_url(self, client_id: str, redirect_uri: str, state: str) -> str:
        raise NotImplementedError("Add the COROS OAuth URL from the partner docs")

    def parse_webhook(self, payload: dict) -> list[ActivityRef]:
        # TODO(partner docs): map COROS push fields. Expected: user id, activity id, FIT download URL.
        refs = []
        for item in payload.get("sportDataList", []):
            if item.get("fitUrl"):
                refs.append(ActivityRef(self.key, str(item.get("openId", "")), str(item.get("labelId", "")), item["fitUrl"]))
        return refs

    def download(self, ref: ActivityRef, access_token: str | None, http: HttpGet) -> bytes:
        return http(ref.file_url, {})
