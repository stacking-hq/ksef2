"""Offline FA(3) schema validation shared by builders and XML readers."""

from functools import lru_cache
from pathlib import Path

from lxml import etree


@lru_cache(maxsize=1)
def load_fa3_schema() -> etree.XMLSchema:
    """Load the bundled XSD without network access."""
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    return etree.XMLSchema(
        etree.parse(str(Path(__file__).parent / "definitions" / "schemat.xsd"), parser)
    )
