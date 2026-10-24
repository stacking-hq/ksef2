"""Deprecated compatibility shim for ``ksef2.clients.base``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.base import *  # noqa: F403

alias_client_modules()
