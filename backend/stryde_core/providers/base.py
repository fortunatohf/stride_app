from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol

from ..importers import import_file
from ..track import Source, Track

# Injected HTTP GET so providers are testable without network: (url, headers) -> response bytes.
HttpGet = Callable[[str, dict], bytes]


class ProviderStatus(str, Enum):
    READY = "ready"  # implemented and tested against the documented API
    NEEDS_KEYS = "needs_keys"  # implemented; waiting for developer approval / credentials
    SCAFFOLD = "scaffold"  # interface only; fill in once partner docs are available


@dataclass(frozen=True)
class ActivityRef:
    provider: str
    external_user_id: str
    external_id: str
    file_url: str
    file_type: str = "FIT"
    manual: bool = False
    extra: dict = field(default_factory=dict)


class Provider(Protocol):
    key: str
    name: str
    source: Source
    status: ProviderStatus

    def authorize_url(self, client_id: str, redirect_uri: str, state: str) -> str: ...
    def parse_webhook(self, payload: dict) -> list[ActivityRef]: ...
    def download(self, ref: ActivityRef, access_token: str | None, http: HttpGet) -> bytes: ...
    def to_track(self, ref: ActivityRef, data: bytes) -> Track: ...


class FileProviderMixin:
    """Shared: most brands deliver a FIT/GPX/TCX file, which the importers already understand."""

    source: Source

    def to_track(self, ref: ActivityRef, data: bytes) -> Track:
        tr = import_file(data, f"activity.{ref.file_type.lower()}", source=self.source)
        tr.external_id = ref.external_id
        tr.manual = tr.manual or ref.manual
        return tr
