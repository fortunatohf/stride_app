"""Watch-brand cloud integrations. Each provider turns a webhook into activity refs, downloads the file,
and hands it to an importer, so every brand ends up as the same `Track`."""

from __future__ import annotations

from .base import ActivityRef, HttpGet, Provider, ProviderStatus
from .coros import CorosProvider
from .garmin import GarminProvider
from .polar import PolarProvider
from .suunto import SuuntoProvider

REGISTRY: dict[str, Provider] = {p.key: p for p in (GarminProvider(), PolarProvider(), CorosProvider(), SuuntoProvider())}

__all__ = ["ActivityRef", "HttpGet", "Provider", "ProviderStatus", "REGISTRY"]
