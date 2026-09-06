"""Pluggable side-effect adapters (email, file storage).

Each sub-package exposes a Protocol in ``base.py`` plus one module per provider
(selected by environment, see ``docs/PLAN.md`` section 6). Every provider module
exposes ``create_adapter(settings)``. Test doubles live in ``tests/fakes``.
"""
