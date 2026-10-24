"""Deprecated compatibility shim for ``ksef2.clients.session_management``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.session_management import *  # noqa: F403

alias_client_modules()
