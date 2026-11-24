"""Convert any activity format into a `Track`.

Use `import_file(data, filename)` for uploaded files, or the specific `from_*` functions.
"""

from __future__ import annotations

from ..track import Source, Track
from .fit import from_fit
from .gpx import from_gpx
from .health import from_health_connect, from_healthkit
from .tcx import from_tcx

__all__ = ["from_fit", "from_gpx", "from_tcx", "from_healthkit", "from_health_connect", "import_file", "UnsupportedFile"]


class UnsupportedFile(ValueError):
    pass


def import_file(data: bytes, filename: str = "", source: Source = Source.FILE) -> Track:
    """Detect the format from content (falls back to the extension) and parse it."""
    head = data[:64]
    name = filename.lower()
    if len(head) >= 12 and head[8:12] == b".FIT" or name.endswith(".fit"):
        return from_fit(data, source=source)
    text_head = data[:2048].decode("utf-8", errors="ignore").lower()
    if "<gpx" in text_head or name.endswith(".gpx"):
        return from_gpx(data, source=source)
    if "trainingcenterdatabase" in text_head or name.endswith(".tcx"):
        return from_tcx(data, source=source)
    raise UnsupportedFile("Upload a .FIT, .GPX or .TCX file")
