from functools import lru_cache
from pathlib import Path

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2._infra.schema.fa3.models.schemat import Faktura
from ksef2._services.builders.fa3.root import StandardInvoiceBuilder


SCHEMA_PATH = Path(__file__).parents[3] / "schemas" / "FA3" / "schemat.xsd"


def sample_path(name: str) -> Path:
    return Path(__file__).parents[3] / "schemas" / "FA3" / "samples" / name


def load_sample(name: Path) -> Faktura:
    parser = XmlParser()
    with open(name, "rb") as f:
        return parser.from_bytes(f.read(), Faktura)


@lru_cache(maxsize=1)
def load_fa3_schema() -> etree.XMLSchema:
    """Compile the checked-in FA(3) XSD used by builder contract tests."""
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    return etree.XMLSchema(etree.parse(str(SCHEMA_PATH), parser))


def serialize_and_validate(builder: StandardInvoiceBuilder) -> bytes:
    """Serialize builder output and assert that it conforms to the FA(3) XSD."""
    xml = builder.to_xml().encode("utf-8")
    document = etree.fromstring(
        xml,
        parser=etree.XMLParser(no_network=True, resolve_entities=False),
    )
    load_fa3_schema().assertValid(document)
    return xml
