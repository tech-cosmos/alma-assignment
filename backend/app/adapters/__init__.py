"""Pluggable side-effect adapters (email, file storage).

Each sub-package exposes a Protocol in ``base.py`` plus concrete
implementations selected by environment (see ``docs/PLAN.md`` section 6)
and a ``build_*_adapter`` factory. Test doubles live in ``tests/fakes``.
"""
