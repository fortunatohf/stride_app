import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def _fernet() -> Fernet:
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        # Dev fallback: derive from SECRET_KEY. Always set FIELD_ENCRYPTION_KEY in production.
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedTextField(models.TextField):
    """Stores text encrypted at rest (used for watch-platform OAuth tokens)."""

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        return _fernet().decrypt(value.encode()).decode()

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return _fernet().encrypt(str(value).encode()).decode()
