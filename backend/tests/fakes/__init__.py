"""In-memory test doubles for the adapters. Import from ``tests.fakes``."""

from .email import FakeEmailAdapter
from .storage import FakeStorageAdapter

__all__ = ["FakeEmailAdapter", "FakeStorageAdapter"]
