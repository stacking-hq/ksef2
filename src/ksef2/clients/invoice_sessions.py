"""Deprecated compatibility shim for ``ksef2.clients.invoice_sessions``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.invoice_sessions import *  # noqa: F403

alias_client_modules()
