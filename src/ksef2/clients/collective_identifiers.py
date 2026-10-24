"""Deprecated compatibility shim for ``ksef2.clients.collective_identifiers``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients.collective_identifiers import *  # noqa: F403

alias_client_modules()
