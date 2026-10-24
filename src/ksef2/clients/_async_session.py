"""Deprecated compatibility shim for ``ksef2.clients._async_session``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients._async_session import *  # noqa: F403

alias_client_modules()
