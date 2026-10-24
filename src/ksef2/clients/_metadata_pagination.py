"""Deprecated compatibility shim for ``ksef2.clients._metadata_pagination``."""

from ksef2._legacy_imports import alias_client_modules
from ksef2._clients._metadata_pagination import *  # noqa: F403

alias_client_modules()
