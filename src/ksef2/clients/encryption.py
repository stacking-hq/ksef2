"""Deprecated compatibility shim for ``ksef2.clients.encryption``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.encryption import *  # noqa: F403

alias_client_modules()
