import os
import random
from pathlib import Path

_MARKER = "pyproject.toml"
EXAMPLE_INVOICE_XML_ENV = "KSEF2_EXAMPLE_INVOICE_XML"
EXAMPLE_SELLER_NIP_ENV = "KSEF2_EXAMPLE_SELLER_NIP"
NIP_WEIGHTS = (6, 5, 7, 2, 3, 4, 5, 6, 7)
PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)


def repo_root() -> Path:
    """Find the repository root by walking up from this file looking for pyproject.toml."""
    for parent in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (parent / _MARKER).exists():
            return parent
    raise FileNotFoundError("Could not find repo root")


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    raise RuntimeError(f"Set {name} before running this example.")


def example_invoice_xml_path() -> Path:
    return Path(required_env(EXAMPLE_INVOICE_XML_ENV)).expanduser()


def example_seller_nip() -> str:
    return required_env(EXAMPLE_SELLER_NIP_ENV)


def generate_example_nip(rng: random.Random | None = None) -> str:
    """Return a random valid NIP for TEST-only examples."""
    generator = rng or random.Random()
    while True:
        digits = [generator.randint(1, 9)]
        second, third = generator.randint(0, 9), generator.randint(0, 9)
        if second == 0 and third == 0:
            third = generator.randint(1, 9)
        digits.extend([second, third])
        digits.extend(generator.randint(0, 9) for _ in range(6))
        checksum = (
            sum(digit * weight for digit, weight in zip(digits, NIP_WEIGHTS)) % 11
        )
        if checksum < 10:
            return "".join(map(str, (*digits, checksum)))


def generate_example_pesel(
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    rng: random.Random | None = None,
) -> str:
    """Return a random valid PESEL for TEST-only examples."""
    generator = rng or random.Random()
    birth_year = year if year is not None else generator.randint(1900, 2099)
    birth_month = month if month is not None else generator.randint(1, 12)
    birth_day = day if day is not None else generator.randint(1, 28)
    century_offset = {18: 80, 19: 0, 20: 20, 21: 40, 22: 60}[birth_year // 100]
    year_digits = birth_year % 100
    month_digits = birth_month + century_offset
    digits = [
        year_digits // 10,
        year_digits % 10,
        month_digits // 10,
        month_digits % 10,
        birth_day // 10,
        birth_day % 10,
        *(generator.randint(0, 9) for _ in range(4)),
    ]
    checksum = (
        10 - sum(digit * weight for digit, weight in zip(digits, PESEL_WEIGHTS)) % 10
    ) % 10
    return "".join(map(str, (*digits, checksum)))
