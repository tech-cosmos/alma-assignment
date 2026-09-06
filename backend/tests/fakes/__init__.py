"""In-memory test doubles for the adapters. Import from ``tests.fakes``."""

from .email import FakeEmailAdapter, SentEmail
from .storage import FakeStorageAdapter, StoredObject

__all__ = ["FakeEmailAdapter", "FakeStorageAdapter", "SentEmail", "StoredObject"]
