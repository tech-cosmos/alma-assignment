"""Storage adapters. ``app.api.deps`` selects one by ``STORAGE_PROVIDER`` and calls the
provider module's ``create_adapter(settings)``."""

from .base import StorageAdapter

STORAGE_PROVIDERS = ("local", "s3")

__all__ = ["STORAGE_PROVIDERS", "StorageAdapter"]
