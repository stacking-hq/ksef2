from pathlib import Path
from xsdata.formats.dataclass.parsers import XmlParser
from ksef2.infra.schema.fa3.models.schemat import Faktura


def sample_path(name: str) -> Path:
    return Path(__file__).parents[3] / "schemas" / "FA3" / "samples" / name


def load_sample(name: Path) -> Faktura:
    parser = XmlParser()
    with open(name, "rb") as f:
        return parser.from_bytes(f.read(), Faktura)
