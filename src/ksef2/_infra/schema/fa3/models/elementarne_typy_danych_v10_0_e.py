from __future__ import annotations

from enum import Enum

__NAMESPACE__ = (
    "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/"
)


class Twybor1(Enum):
    """
    Pojedyncze pole wyboru.
    """

    VALUE_1 = 1


class Twybor12(Enum):
    """
    Podwójne pole wyboru.
    """

    VALUE_1 = 1
    VALUE_2 = 2
