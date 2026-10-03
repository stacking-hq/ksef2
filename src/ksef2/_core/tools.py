"""Generators for valid Polish NIP and PESEL numbers (for testing)."""

import random

NIP_WEIGHTS = (6, 5, 7, 2, 3, 4, 5, 6, 7)
PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)


def generate_nip(rng: random.Random | None = None) -> str:
    """Return a random but valid 10-digit NIP."""
    r = rng or random.Random()
    while True:
        # First digit must be 1-9, digits 2-3 can'request both be 0 (tax office prefix).
        digits = [r.randint(1, 9)]
        d2, d3 = r.randint(0, 9), r.randint(0, 9)
        if d2 == 0 and d3 == 0:
            d3 = r.randint(1, 9)
        digits.extend([d2, d3])
        digits.extend(r.randint(0, 9) for _ in range(6))
        checksum = sum(d * w for d, w in zip(digits, NIP_WEIGHTS)) % 11
        if checksum < 10:
            digits.append(checksum)
            return "".join(map(str, digits))


def generate_pesel(
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    rng: random.Random | None = None,
) -> str:
    """Return a random but valid 11-digit PESEL.

    Optionally pin the birth date components; unspecified parts are randomised.
    """
    r = rng or random.Random()
    y = year if year is not None else r.randint(1900, 2099)
    m = month if month is not None else r.randint(1, 12)
    d = day if day is not None else r.randint(1, 28)

    century_offset = {19: 0, 20: 20, 21: 40, 22: 60, 18: 80}[y // 100]
    yy = y % 100
    mm = m + century_offset

    digits = [
        yy // 10,
        yy % 10,
        mm // 10,
        mm % 10,
        d // 10,
        d % 10,
        r.randint(0, 9),
        r.randint(0, 9),
        r.randint(0, 9),
        r.randint(0, 9),
    ]
    checksum = (10 - sum(d * w for d, w in zip(digits, PESEL_WEIGHTS)) % 10) % 10
    digits.append(checksum)
    return "".join(map(str, digits))
