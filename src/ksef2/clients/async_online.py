"""Deprecated compatibility shim for ``ksef2.clients.async_online``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.async_online import *  # noqa: F403

alias_client_modules()
