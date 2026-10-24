"""Deprecated compatibility shim for ``ksef2.clients.async_base``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.async_base import *  # noqa: F403

alias_client_modules()
