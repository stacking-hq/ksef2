from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from xsdata.models.datatype import XmlDateTime

from .elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from .kody_krajow_v10_0_e import TkodKraju

__NAMESPACE__ = "http://crd.gov.pl/wzor/2025/06/25/13775/"


@dataclass(kw_only=True)
class FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu:
    """
    Attributes:
        p_22_a: Data dopuszczenia nowego środka transportu do użytku
        p_nr_wiersza_nst: Numer wiersza faktury, w którym wykazano
            dostawę nowego środka transportu
        p_22_bmk: Marka nowego środka transportu
        p_22_bmd: Model nowego środka transportu
        p_22_bk: Kolor nowego środka transportu
        p_22_bnr: Numer rejestracyjny nowego środka transportu
        p_22_brp: Rok produkcji nowego środka transportu
        p_22_b: Jeśli dostawa dotyczy pojazdów lądowych, o których mowa
            w art. 2 pkt 10 lit. a ustawy, należy podać przebieg pojazdu
        p_22_b1: Jeśli dostawa dotyczy pojazdów lądowych, o których mowa
            w art. 2 pkt 10 lit. a ustawy, można podać numer VIN
        p_22_b2: Jeśli dostawa dotyczy pojazdów lądowych, o których mowa
            w art. 2 pkt 10 lit. a ustawy, można podać numer nadwozia
        p_22_b3: Jeśli dostawa dotyczy pojazdów lądowych, o których mowa
            w art. 2 pkt 10 lit. a ustawy, można podać numer podwozia
        p_22_b4: Jeśli dostawa dotyczy pojazdów lądowych, o których mowa
            w art. 2 pkt 10 lit. a ustawy, można podać numer ramy
        p_22_bt: Jeśli dostawa dotyczy pojazdów lądowych, o których mowa
            w art. 2 pkt 10 lit. a ustawy, można podać typ nowego środka
            transportu
        p_22_c: Jeśli dostawa dotyczy jednostek pływających, o których
            mowa w art. 2 pkt 10 lit. b ustawy, należy podać liczbę
            godzin roboczych używania nowego środka transportu
        p_22_c1: Jeśli dostawa dotyczy jednostek pływających, o których
            mowa w art. 2 pkt 10 lit. b ustawy, można podać numer
            kadłuba nowego środka transportu
        p_22_d: Jeśli dostawa dotyczy statków powietrznych, o których
            mowa w art. 2 pkt 10 lit. c ustawy, należy podać liczbę
            godzin roboczych używania nowego środka transportu
        p_22_d1: Jeśli dostawa dotyczy statków powietrznych, o których
            mowa w art. 2 pkt 10 lit. c ustawy, można podać numer
            fabryczny nowego środka transportu
    """

    class Meta:
        global_type = False

    p_22_a: str = field(
        metadata={
            "name": "P_22A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    p_nr_wiersza_nst: int = field(
        metadata={
            "name": "P_NrWierszaNST",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_exclusive": 0,
            "total_digits": 14,
            "white_space": "collapse",
        }
    )
    p_22_bmk: None | str = field(
        default=None,
        metadata={
            "name": "P_22BMK",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_bmd: None | str = field(
        default=None,
        metadata={
            "name": "P_22BMD",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_bk: None | str = field(
        default=None,
        metadata={
            "name": "P_22BK",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_bnr: None | str = field(
        default=None,
        metadata={
            "name": "P_22BNR",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_brp: None | str = field(
        default=None,
        metadata={
            "name": "P_22BRP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_b: None | str = field(
        default=None,
        metadata={
            "name": "P_22B",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_b1: None | str = field(
        default=None,
        metadata={
            "name": "P_22B1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_b2: None | str = field(
        default=None,
        metadata={
            "name": "P_22B2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_b3: None | str = field(
        default=None,
        metadata={
            "name": "P_22B3",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_b4: None | str = field(
        default=None,
        metadata={
            "name": "P_22B4",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_bt: None | str = field(
        default=None,
        metadata={
            "name": "P_22BT",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_c: None | str = field(
        default=None,
        metadata={
            "name": "P_22C",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_c1: None | str = field(
        default=None,
        metadata={
            "name": "P_22C1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_d: None | str = field(
        default=None,
        metadata={
            "name": "P_22D",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_22_d1: None | str = field(
        default=None,
        metadata={
            "name": "P_22D1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaFaOkresFa:
    """
    Attributes:
        p_6_od: Data początkowa okresu, którego dotyczy faktura
        p_6_do: Data końcowa okresu, którego dotyczy faktura - data
            dokonania lub zakończenia dostawy towarów lub wykonania
            usługi
    """

    class Meta:
        global_type = False

    p_6_od: str = field(
        metadata={
            "name": "P_6_Od",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    p_6_do: str = field(
        metadata={
            "name": "P_6_Do",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )


@dataclass(kw_only=True)
class FakturaFaPlatnoscSkonto:
    """
    Attributes:
        warunki_skonta: Warunki, które nabywca powinien spełnić, aby
            skorzystać ze skonta
        wysokosc_skonta: Wysokość skonta
    """

    class Meta:
        global_type = False

    warunki_skonta: str = field(
        metadata={
            "name": "WarunkiSkonta",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )
    wysokosc_skonta: str = field(
        metadata={
            "name": "WysokoscSkonta",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


@dataclass(kw_only=True)
class FakturaFaPlatnoscTerminPlatnosciTerminOpis:
    class Meta:
        global_type = False

    ilosc: int = field(
        metadata={
            "name": "Ilosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    jednostka: str = field(
        metadata={
            "name": "Jednostka",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 50,
        }
    )
    zdarzenie_poczatkowe: str = field(
        metadata={
            "name": "ZdarzeniePoczatkowe",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


@dataclass(kw_only=True)
class FakturaFaRozliczenieObciazenia:
    """
    Attributes:
        kwota: Kwota doliczona do kwoty wykazanej w polu P_15
        powod: Powód obciążenia
    """

    class Meta:
        global_type = False

    kwota: str = field(
        metadata={
            "name": "Kwota",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        }
    )
    powod: str = field(
        metadata={
            "name": "Powod",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


@dataclass(kw_only=True)
class FakturaFaRozliczenieOdliczenia:
    """
    Attributes:
        kwota: Kwota odliczona od kwoty wykazanej w polu P_15
        powod: Powód odliczenia
    """

    class Meta:
        global_type = False

    kwota: str = field(
        metadata={
            "name": "Kwota",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        }
    )
    powod: str = field(
        metadata={
            "name": "Powod",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


@dataclass(kw_only=True)
class FakturaFaWarunkiTransakcjiUmowy:
    """
    Attributes:
        data_umowy: Data umowy
        nr_umowy: Numer umowy
    """

    class Meta:
        global_type = False

    data_umowy: None | str = field(
        default=None,
        metadata={
            "name": "DataUmowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": "1990-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        },
    )
    nr_umowy: None | str = field(
        default=None,
        metadata={
            "name": "NrUmowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaFaWarunkiTransakcjiZamowienia:
    """
    Attributes:
        data_zamowienia: Data zamówienia
        nr_zamowienia: Numer zamówienia
    """

    class Meta:
        global_type = False

    data_zamowienia: None | str = field(
        default=None,
        metadata={
            "name": "DataZamowienia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": "1990-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        },
    )
    nr_zamowienia: None | str = field(
        default=None,
        metadata={
            "name": "NrZamowienia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaFaZaliczkaCzesciowa:
    """
    Attributes:
        p_6_z: Data otrzymania płatności, o której mowa w art. 106b ust.
            1 pkt 4 ustawy
        p_15_z: Kwota płatności, o której mowa w art. 106b ust. 1 pkt 4
            ustawy, składająca się na kwotę w polu P_15. W przypadku
            faktur korygujących  - korekta kwoty wynikającej z faktury
            korygowanej
        kurs_waluty_zw: Kurs waluty stosowany do wyliczenia kwoty
            podatku w przypadkach, o których mowa w dziale VI ustawy
    """

    class Meta:
        global_type = False

    p_6_z: str = field(
        metadata={
            "name": "P_6Z",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    p_15_z: str = field(
        metadata={
            "name": "P_15Z",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        }
    )
    kurs_waluty_zw: None | str = field(
        default=None,
        metadata={
            "name": "KursWalutyZW",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )


@dataclass(kw_only=True)
class FakturaPodmiot1DaneKontaktowe:
    """
    Attributes:
        email: Adres e-mail podatnika
        telefon: Numer telefonu podatnika
    """

    class Meta:
        global_type = False

    email: None | str = field(
        default=None,
        metadata={
            "name": "Email",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 3,
            "max_length": 255,
            "pattern": r"(.)+@(.)+",
        },
    )
    telefon: None | str = field(
        default=None,
        metadata={
            "name": "Telefon",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 16,
        },
    )


@dataclass(kw_only=True)
class FakturaPodmiot2DaneKontaktowe:
    """
    Attributes:
        email: Adres e-mail nabywcy
        telefon: Numer telefonu nabywcy
    """

    class Meta:
        global_type = False

    email: None | str = field(
        default=None,
        metadata={
            "name": "Email",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 3,
            "max_length": 255,
            "pattern": r"(.)+@(.)+",
        },
    )
    telefon: None | str = field(
        default=None,
        metadata={
            "name": "Telefon",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 16,
        },
    )


class FakturaPodmiot2Gv(Enum):
    """
    Attributes:
        VALUE_1: Tak
        VALUE_2: Nie
    """

    VALUE_1 = 1
    VALUE_2 = 2


class FakturaPodmiot2Jst(Enum):
    """
    Attributes:
        VALUE_1: Tak
        VALUE_2: Nie
    """

    VALUE_1 = 1
    VALUE_2 = 2


@dataclass(kw_only=True)
class FakturaPodmiot3DaneKontaktowe:
    """
    Attributes:
        email: Adres e-mail podmiotu trzeciego
        telefon: Numer telefonu podmiotu trzeciego
    """

    class Meta:
        global_type = False

    email: None | str = field(
        default=None,
        metadata={
            "name": "Email",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 3,
            "max_length": 255,
            "pattern": r"(.)+@(.)+",
        },
    )
    telefon: None | str = field(
        default=None,
        metadata={
            "name": "Telefon",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 16,
        },
    )


@dataclass(kw_only=True)
class FakturaPodmiotUpowaznionyDaneKontaktowe:
    """
    Attributes:
        email_pu: Adres e-mail podmiotu upoważnionego
        telefon_pu: Numer telefonu podmiotu upoważnionego
    """

    class Meta:
        global_type = False

    email_pu: None | str = field(
        default=None,
        metadata={
            "name": "EmailPU",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 3,
            "max_length": 255,
            "pattern": r"(.)+@(.)+",
        },
    )
    telefon_pu: None | str = field(
        default=None,
        metadata={
            "name": "TelefonPU",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 16,
        },
    )


@dataclass(kw_only=True)
class FakturaStopkaInformacje:
    """
    Attributes:
        stopka_faktury: Stopka faktury
    """

    class Meta:
        global_type = False

    stopka_faktury: None | str = field(
        default=None,
        metadata={
            "name": "StopkaFaktury",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 3500,
        },
    )


@dataclass(kw_only=True)
class FakturaStopkaRejestry:
    """
    Attributes:
        pelna_nazwa: Pełna nazwa
        krs: KRS
        regon: REGON
        bdo: BDO
    """

    class Meta:
        global_type = False

    pelna_nazwa: None | str = field(
        default=None,
        metadata={
            "name": "PelnaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    krs: None | str = field(
        default=None,
        metadata={
            "name": "KRS",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"\d{10}",
        },
    )
    regon: None | str = field(
        default=None,
        metadata={
            "name": "REGON",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"\d{14}",
        },
    )
    bdo: None | str = field(
        default=None,
        metadata={
            "name": "BDO",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 9,
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychMetaDane:
    """
    Attributes:
        zklucz: Klucz
        zwartosc: Wartość
    """

    class Meta:
        global_type = False

    zklucz: str = field(
        metadata={
            "name": "ZKlucz",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )
    zwartosc: str = field(
        metadata={
            "name": "ZWartosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabelaSuma:
    """
    Attributes:
        skom: Zawartość pola
    """

    class Meta:
        global_type = False

    skom: list[str] = field(
        default_factory=list,
        metadata={
            "name": "SKom",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 20,
            "min_length": 0,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabelaTmetaDane:
    """
    Attributes:
        tklucz: Klucz
        twartosc: Wartość
    """

    class Meta:
        global_type = False

    tklucz: str = field(
        metadata={
            "name": "TKlucz",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )
    twartosc: str = field(
        metadata={
            "name": "TWartosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabelaTnaglowekKolNkom:
    class Meta:
        global_type = False

    value: str = field(
        default="",
        metadata={
            "required": True,
            "min_length": 0,
            "max_length": 256,
        },
    )


class FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp(Enum):
    DATE = "date"
    DATETIME = "datetime"
    DEC = "dec"
    INT = "int"
    TIME = "time"
    TXT = "txt"


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabelaWiersz:
    """
    Attributes:
        wkom: Zawartość pola
    """

    class Meta:
        global_type = False

    wkom: list[str] = field(
        default_factory=list,
        metadata={
            "name": "WKom",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 20,
            "min_length": 0,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTekst:
    """
    Attributes:
        akapit: Opis
    """

    class Meta:
        global_type = False

    akapit: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Akapit",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 10,
            "min_length": 1,
            "max_length": 512,
        },
    )


class TformaPlatnosci(Enum):
    """
    Typy form płatności.

    Attributes:
        VALUE_1: Gotówka
        VALUE_2: Karta
        VALUE_3: Bon
        VALUE_4: Czek
        VALUE_5: Kredyt
        VALUE_6: Przelew
        VALUE_7: Mobilna
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7


class Tgtu(Enum):
    """
    Oznaczenie dotyczące dostawy towarów i świadczenia usług.

    Attributes:
        GTU_01: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            a rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_02: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            b rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_03: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            c rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_04: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            d rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_05: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            e rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_06: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            f rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_07: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            g rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_08: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            h rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_09: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            i rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_10: Dostawa towarów, o których mowa w § 10 ust. 3 pkt 1 lit.
            j rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_11: Świadczenie usług, o których mowa w § 10 ust. 3 pkt 2
            lit. a rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_12: Świadczenie usług, o których mowa w § 10 ust. 3 pkt 2
            lit. b rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        GTU_13: Świadczenie usług, o których mowa w § 10 ust. 3 pkt 2
            lit. c rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
    """

    GTU_01 = "GTU_01"
    GTU_02 = "GTU_02"
    GTU_03 = "GTU_03"
    GTU_04 = "GTU_04"
    GTU_05 = "GTU_05"
    GTU_06 = "GTU_06"
    GTU_07 = "GTU_07"
    GTU_08 = "GTU_08"
    GTU_09 = "GTU_09"
    GTU_10 = "GTU_10"
    GTU_11 = "GTU_11"
    GTU_12 = "GTU_12"
    GTU_13 = "GTU_13"


@dataclass(kw_only=True)
class TkluczWartosc:
    """
    Typ złożony, klucz-wartość.

    Attributes:
        nr_wiersza: Numer wiersza podany w polu NrWierszaFa lub
            NrWierszaZam, jeśli informacja odnosi się wyłącznie do danej
            pozycji faktury
        klucz: Klucz
        wartosc: Wartość
    """

    class Meta:
        name = "TKluczWartosc"

    nr_wiersza: None | int = field(
        default=None,
        metadata={
            "name": "NrWiersza",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_exclusive": 0,
            "total_digits": 14,
            "white_space": "collapse",
        },
    )
    klucz: str = field(
        metadata={
            "name": "Klucz",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )
    wartosc: str = field(
        metadata={
            "name": "Wartosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )


class TkodFormularza(Enum):
    """
    Symbol wzoru formularza.
    """

    FA = "FA"


class TkodWaluty(Enum):
    """
    Słownik kodów walut.

    Attributes:
        AED: DIRHAM ZEA
        AFN: AFGANI
        ALL: LEK
        AMD: DRAM
        ANG: GULDEN ANTYLI HOLENDERSKICH
        AOA: KWANZA
        ARS: PESO ARGENTYŃSKIE
        AUD: DOLAR AUSTRALIJSKI
        AWG: GULDEN ARUBAŃSKI
        AZN: MANAT AZERBEJDŻAŃSKI
        BAM: MARKA ZAMIENNA
        BBD: DOLAR BARBADOSKI
        BDT: TAKA
        BGN: LEW
        BHD: DINAR BAHRAJSKI
        BIF: FRANK BURUNDYJSKI
        BMD: DOLAR BERMUDZKI
        BND: DOLAR BRUNEJSKI
        BOB: BOLIWIANO
        BOV: BOLIWIANO MVDOL
        BRL: REAL
        BSD: DOLAR BAHAMSKI
        BTN: NGULTRUM
        BWP: PULA
        BYN: RUBEL BIAŁORUSKI
        BZD: DOLAR BELIZEŃSKI
        CAD: DOLAR KANADYJSKI
        CDF: FRANK KONGIJSKI
        CHE: FRANK SZWAJCARSKI VIR EURO
        CHF: FRANK SZWAJCARSKI
        CHW: FRANK SZWAJCARSKI VIR FRANK
        CLF: JEDNOSTKA ROZLICZENIOWA CHILIJSKA
        CLP: PESO CHILIJSKIE
        CNY: YUAN RENMINBI
        COP: PESO KOLUMBIJSKIE
        COU: UNIDAD DE VALOR REAL KOLUMBILSKIE
        CRC: COLON KOSTARYKAŃSKI
        CUC: PESO WYMIENIALNE
        CUP: PESO KUBAŃSKIE
        CVE: ESCUDO REPUBLIKI ZIELONEGO PRZYLĄDKA
        CZK: KORONA CZESKA
        DJF: FRANK DŻIBUTI
        DKK: KORONA DUŃSKA
        DOP: PESO DOMINIKAŃSKIE
        DZD: DINAR ALGIERSKI
        EGP: FUNT EGIPSKI
        ERN: NAKFA
        ETB: BIRR
        EUR: EURO
        FJD: DOLAR FIDŻI
        FKP: FUNT FALKLANDZKI
        GBP: FUNT SZTERLING
        GEL: LARI
        GGP: FUNT GUERNSEY
        GHS: GHANA CEDI
        GIP: FUNT GIBRALTARSKI
        GMD: DALASI
        GNF: FRANK GWINEJSKI
        GTQ: QUETZAL
        GYD: DOLAR GUJAŃSKI
        HKD: DOLAR HONGKONGU
        HNL: LEMPIRA
        HRK: KUNA
        HTG: GOURDE
        HUF: FORINT
        IDR: RUPIA INDONEZYJSKA
        ILS: SZEKEL
        IMP: FUNT MANX
        INR: RUPIA INDYJSKA
        IQD: DINAR IRACKI
        IRR: RIAL IRAŃSKI
        ISK: KORONA ISLANDZKA
        JEP: FUNT JERSEY
        JMD: DOLAR JAMAJSKI
        JOD: DINAR JORDAŃSKI
        JPY: JEN
        KES: SZYLING KENIJSKI
        KGS: SOM
        KHR: RIEL
        KMF: FRANK KOMORÓW
        KPW: WON PÓŁNOCNO­KOREAŃSKI
        KRW: WON POŁUDNIOWO­KOREAŃSKI
        KWD: DINAR KUWEJCKI
        KYD: DOLAR KAJMAŃSKI
        KZT: TENGE
        LAK: KIP
        LBP: FUNT LIBAŃSKI
        LKR: RUPIA LANKIJSKA
        LRD: DOLAR LIBERYJSKI
        LSL: LOTI
        LYD: DINAR LIBIJSKI
        MAD: DIRHAM MAROKAŃSKI
        MDL: LEJ MOŁDAWII
        MGA: ARIARY
        MKD: DENAR
        MMK: KYAT
        MNT: TUGRIK
        MOP: PATACA
        MRU: OUGUIYA
        MUR: RUPIA MAURITIUSU
        MVR: RUPIA MALEDIWSKA
        MWK: KWACHA MALAWIJSKA
        MXN: PESO MEKSYKAŃSKIE
        MXV: UNIDAD DE INVERSION (UDI) MEKSYKAŃSKIE
        MYR: RINGGIT
        MZN: METICAL
        NAD: DOLAR NAMIBIJSKI
        NGN: NAIRA
        NIO: CORDOBA ORO
        NOK: KORONA NORWESKA
        NPR: RUPIA NEPALSKA
        NZD: DOLAR NOWOZELANDZKI
        OMR: RIAL OMAŃSKI
        PAB: BALBOA
        PEN: SOL
        PGK: KINA
        PHP: PESO FILIPIŃSKIE
        PKR: RUPIA PAKISTAŃSKA
        PLN: ZŁOTY
        PYG: GUARANI
        QAR: RIAL KATARSKI
        RON: LEJ RUMUŃSKI
        RSD: DINAR SERBSKI
        RUB: RUBEL ROSYJSKI
        RWF: FRANK RWANDYJSKI
        SAR: RIAL SAUDYJSKI
        SBD: DOLAR WYSP SALOMONA
        SCR: RUPIA SESZELSKA
        SDG: FUNT SUDAŃSKI
        SEK: KORONA SZWEDZKA
        SGD: DOLAR SINGAPURSKI
        SHP: FUNT ŚWIĘTEJ HELENY (ŚWIĘTA HELENA I WYSPA
            WNIEBOWSTĄPIENIA)
        SLL: LEONE
        SOS: SZYLING SOMALIJSKI
        SRD: DOLAR SURINAMSKI
        SSP: FUNT POŁUDNIOWOSUDAŃSKI
        STN: DOBRA
        SVC: COLON SALWADORSKI (SV1)
        SYP: FUNT SYRYJSKI
        SZL: LILANGENI
        THB: BAT
        TJS: SOMONI
        TMT: MANAT TURKMEŃSKI
        TND: DINAR TUNEZYJSKI
        TOP: PAANGA
        TRY: LIRA TURECKA
        TTD: DOLAR TRYNIDADU I TOBAGO
        TWD: NOWY DOLAR TAJWAŃSKI
        TZS: SZYLING TANZAŃSKI
        UAH: HRYWNA
        UGX: SZYLING UGANDYJSKI
        USD: DOLAR AMERYKAŃSKI
        USN: DOLAR AMERYKAŃSKI (NEXT DAY)
        UYI: PESO EN UNIDADES INDEXADAS URUGWAJSKIE
        UYU: PESO URUGWAJSKIE
        UYW: PESO EN UNIDADES INDEXADAS URUGWAJSKIE
        UZS: SUM
        VES: BOLIWAR SOBERANO
        VND: DONG
        VUV: VATU
        WST: TALA
        XAF: FRANK CFA (BEAC)
        XAG: SREBRO
        XAU: ZŁOTO
        XBA: BOND MARKETS UNIT EUROPEAN COMPOSITE UNIT (EURCO)
        XBB: BOND MARKETS UNIT EUROPEAN MONETARY UNIT (E.M.U.-6)
        XBC: BOND MARKETS UNIT EUROPEAN UNIT OF ACCOUNT 9 (E.U.A.-9)
        XBD: BOND MARKETS UNIT EUROPEAN UNIT OF ACCOUNT 17 (E.U.A.-17)
        XCD: DOLAR WSCHODNIO­KARAIBSKI
        XCG: GULDEN KARAIBSKI
        XDR: SDR MIĘDZYNARODOWY FUNDUSZ WALUTOWY
        XOF: FRANK CFA (BCEAO)
        XPD: PALLAD
        XPF: FRANK CFP
        XPT: PLATYNA
        XSU: SUCRE SISTEMA UNITARIO DE COMPENSACION REGIONAL DE PAGOS
            SUCRE
        XUA: ADB UNIT OF ACCOUNT MEMBER COUNTRIES OF THE AFRICAN
            DEVELOPMENT BANK GROUP
        XXX: BRAK WALUTY
        YER: RIAL JEMEŃSKI
        ZAR: RAND
        ZMW: KWACHA ZAMBIJSKA
        ZWL: DOLAR ZIMBABWE
    """

    AED = "AED"
    AFN = "AFN"
    ALL = "ALL"
    AMD = "AMD"
    ANG = "ANG"
    AOA = "AOA"
    ARS = "ARS"
    AUD = "AUD"
    AWG = "AWG"
    AZN = "AZN"
    BAM = "BAM"
    BBD = "BBD"
    BDT = "BDT"
    BGN = "BGN"
    BHD = "BHD"
    BIF = "BIF"
    BMD = "BMD"
    BND = "BND"
    BOB = "BOB"
    BOV = "BOV"
    BRL = "BRL"
    BSD = "BSD"
    BTN = "BTN"
    BWP = "BWP"
    BYN = "BYN"
    BZD = "BZD"
    CAD = "CAD"
    CDF = "CDF"
    CHE = "CHE"
    CHF = "CHF"
    CHW = "CHW"
    CLF = "CLF"
    CLP = "CLP"
    CNY = "CNY"
    COP = "COP"
    COU = "COU"
    CRC = "CRC"
    CUC = "CUC"
    CUP = "CUP"
    CVE = "CVE"
    CZK = "CZK"
    DJF = "DJF"
    DKK = "DKK"
    DOP = "DOP"
    DZD = "DZD"
    EGP = "EGP"
    ERN = "ERN"
    ETB = "ETB"
    EUR = "EUR"
    FJD = "FJD"
    FKP = "FKP"
    GBP = "GBP"
    GEL = "GEL"
    GGP = "GGP"
    GHS = "GHS"
    GIP = "GIP"
    GMD = "GMD"
    GNF = "GNF"
    GTQ = "GTQ"
    GYD = "GYD"
    HKD = "HKD"
    HNL = "HNL"
    HRK = "HRK"
    HTG = "HTG"
    HUF = "HUF"
    IDR = "IDR"
    ILS = "ILS"
    IMP = "IMP"
    INR = "INR"
    IQD = "IQD"
    IRR = "IRR"
    ISK = "ISK"
    JEP = "JEP"
    JMD = "JMD"
    JOD = "JOD"
    JPY = "JPY"
    KES = "KES"
    KGS = "KGS"
    KHR = "KHR"
    KMF = "KMF"
    KPW = "KPW"
    KRW = "KRW"
    KWD = "KWD"
    KYD = "KYD"
    KZT = "KZT"
    LAK = "LAK"
    LBP = "LBP"
    LKR = "LKR"
    LRD = "LRD"
    LSL = "LSL"
    LYD = "LYD"
    MAD = "MAD"
    MDL = "MDL"
    MGA = "MGA"
    MKD = "MKD"
    MMK = "MMK"
    MNT = "MNT"
    MOP = "MOP"
    MRU = "MRU"
    MUR = "MUR"
    MVR = "MVR"
    MWK = "MWK"
    MXN = "MXN"
    MXV = "MXV"
    MYR = "MYR"
    MZN = "MZN"
    NAD = "NAD"
    NGN = "NGN"
    NIO = "NIO"
    NOK = "NOK"
    NPR = "NPR"
    NZD = "NZD"
    OMR = "OMR"
    PAB = "PAB"
    PEN = "PEN"
    PGK = "PGK"
    PHP = "PHP"
    PKR = "PKR"
    PLN = "PLN"
    PYG = "PYG"
    QAR = "QAR"
    RON = "RON"
    RSD = "RSD"
    RUB = "RUB"
    RWF = "RWF"
    SAR = "SAR"
    SBD = "SBD"
    SCR = "SCR"
    SDG = "SDG"
    SEK = "SEK"
    SGD = "SGD"
    SHP = "SHP"
    SLL = "SLL"
    SOS = "SOS"
    SRD = "SRD"
    SSP = "SSP"
    STN = "STN"
    SVC = "SVC"
    SYP = "SYP"
    SZL = "SZL"
    THB = "THB"
    TJS = "TJS"
    TMT = "TMT"
    TND = "TND"
    TOP = "TOP"
    TRY = "TRY"
    TTD = "TTD"
    TWD = "TWD"
    TZS = "TZS"
    UAH = "UAH"
    UGX = "UGX"
    USD = "USD"
    USN = "USN"
    UYI = "UYI"
    UYU = "UYU"
    UYW = "UYW"
    UZS = "UZS"
    VES = "VES"
    VND = "VND"
    VUV = "VUV"
    WST = "WST"
    XAF = "XAF"
    XAG = "XAG"
    XAU = "XAU"
    XBA = "XBA"
    XBB = "XBB"
    XBC = "XBC"
    XBD = "XBD"
    XCD = "XCD"
    XCG = "XCG"
    XDR = "XDR"
    XOF = "XOF"
    XPD = "XPD"
    XPF = "XPF"
    XPT = "XPT"
    XSU = "XSU"
    XUA = "XUA"
    XXX = "XXX"
    YER = "YER"
    ZAR = "ZAR"
    ZMW = "ZMW"
    ZWL = "ZWL"


class TkodyKrajowUe(Enum):
    """
    Kody krajów członkowskich Unii Europejskiej, w tym kod dla obszaru
    Irlandii Północnej.

    Attributes:
        AT: AUSTRIA
        BE: BELGIA
        BG: BUŁGARIA
        CY: CYPR
        CZ: CZECHY
        DK: DANIA
        EE: ESTONIA
        FI: FINLANDIA
        FR: FRANCJA
        DE: NIEMCY
        EL: GRECJA
        HR: CHORWACJA
        HU: WĘGRY
        IE: IRLANDIA
        IT: WŁOCHY
        LV: ŁOTWA
        LT: LITWA
        LU: LUKSEMBURG
        MT: MALTA
        NL: HOLANDIA
        PL: POLSKA
        PT: PORTUGALIA
        RO: RUMUNIA
        SK: SŁOWACJA
        SI: SŁOWENIA
        ES: HISZPANIA
        SE: SZWECJA
        XI: IRLANDIA PÓŁNOCNA
    """

    AT = "AT"
    BE = "BE"
    BG = "BG"
    CY = "CY"
    CZ = "CZ"
    DK = "DK"
    EE = "EE"
    FI = "FI"
    FR = "FR"
    DE = "DE"
    EL = "EL"
    HR = "HR"
    HU = "HU"
    IE = "IE"
    IT = "IT"
    LV = "LV"
    LT = "LT"
    LU = "LU"
    MT = "MT"
    NL = "NL"
    PL = "PL"
    PT = "PT"
    RO = "RO"
    SK = "SK"
    SI = "SI"
    ES = "ES"
    SE = "SE"
    XI = "XI"


class Tladunek(Enum):
    """
    Typy ładunków.

    Attributes:
        VALUE_1: Bańka
        VALUE_2: Beczka
        VALUE_3: Butla
        VALUE_4: Karton
        VALUE_5: Kanister
        VALUE_6: Klatka
        VALUE_7: Kontener
        VALUE_8: Kosz/koszyk
        VALUE_9: Łubianka
        VALUE_10: Opakowanie zbiorcze
        VALUE_11: Paczka
        VALUE_12: Pakiet
        VALUE_13: Paleta
        VALUE_14: Pojemnik
        VALUE_15: Pojemnik do ładunków masowych stałych
        VALUE_16: Pojemnik do ładunków masowych w postaci płynnej
        VALUE_17: Pudełko
        VALUE_18: Puszka
        VALUE_19: Skrzynia
        VALUE_20: Worek
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7
    VALUE_8 = 8
    VALUE_9 = 9
    VALUE_10 = 10
    VALUE_11 = 11
    VALUE_12 = 12
    VALUE_13 = 13
    VALUE_14 = 14
    VALUE_15 = 15
    VALUE_16 = 16
    VALUE_17 = 17
    VALUE_18 = 18
    VALUE_19 = 19
    VALUE_20 = 20


class TnaglowekWariantFormularza(Enum):
    VALUE_3 = 3


class ToznaczenieProcedury(Enum):
    """
    Oznaczenia dotyczące procedur dla faktur.

    Attributes:
        WSTO_EE: Oznaczenie dotyczące procedury, o której mowa w § 10
            ust. 4 pkt 2a rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        IED: Oznaczenie dotyczące procedury, o której mowa w § 10 ust. 4
            pkt 2b rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        TT_D: Oznaczenie dotyczące procedury, o której mowa w § 10 ust.
            4 pkt 5 rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        I_42: Oznaczenie dotyczące procedury, o której mowa w § 10 ust.
            4 pkt 8 rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        I_63: Oznaczenie dotyczące procedury, o której mowa w § 10 ust.
            4 pkt 9 rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        B_SPV: Oznaczenie dotyczące procedury, o której mowa w § 10 ust.
            4 pkt 10 rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        B_SPV_DOSTAWA: Oznaczenie dotyczące procedury, o której mowa w §
            10 ust. 4 pkt 11 rozporządzenia w sprawie szczegółowego
            zakresu danych zawartych w deklaracjach podatkowych i w
            ewidencji w zakresie podatku od towarów i usług
        B_MPV_PROWIZJA: Oznaczenie dotyczące procedury, o której mowa w
            § 10 ust. 4 pkt 12 rozporządzenia w sprawie szczegółowego
            zakresu danych zawartych w deklaracjach podatkowych i w
            ewidencji w zakresie podatku od towarów i usług
    """

    WSTO_EE = "WSTO_EE"
    IED = "IED"
    TT_D = "TT_D"
    I_42 = "I_42"
    I_63 = "I_63"
    B_SPV = "B_SPV"
    B_SPV_DOSTAWA = "B_SPV_DOSTAWA"
    B_MPV_PROWIZJA = "B_MPV_PROWIZJA"


class ToznaczenieProceduryZ(Enum):
    """
    Oznaczenia dotyczące procedur dla zamówień.

    Attributes:
        WSTO_EE: Oznaczenie dotyczące procedury, o której mowa w § 10
            ust. 4 pkt 2a rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        IED: Oznaczenie dotyczące procedury, o której mowa w § 10 ust. 4
            pkt 2b rozporządzenia w sprawie szczegółowego zakresu danych
            zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        TT_D: Oznaczenie dotyczące procedury, o której mowa w § 10 ust.
            4 pkt 5 rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        B_SPV: Oznaczenie dotyczące procedury, o której mowa w § 10 ust.
            4 pkt 10 rozporządzenia w sprawie szczegółowego zakresu
            danych zawartych w deklaracjach podatkowych i w ewidencji w
            zakresie podatku od towarów i usług
        B_SPV_DOSTAWA: Oznaczenie dotyczące procedury, o której mowa w §
            10 ust. 4 pkt 11 rozporządzenia w sprawie szczegółowego
            zakresu danych zawartych w deklaracjach podatkowych i w
            ewidencji w zakresie podatku od towarów i usług
        B_MPV_PROWIZJA: Oznaczenie dotyczące procedury, o której mowa w
            § 10 ust. 4 pkt 12 rozporządzenia w sprawie szczegółowego
            zakresu danych zawartych w deklaracjach podatkowych i w
            ewidencji w zakresie podatku od towarów i usług
    """

    WSTO_EE = "WSTO_EE"
    IED = "IED"
    TT_D = "TT_D"
    B_SPV = "B_SPV"
    B_SPV_DOSTAWA = "B_SPV_DOSTAWA"
    B_MPV_PROWIZJA = "B_MPV_PROWIZJA"


@dataclass(kw_only=True)
class Tpodmiot1:
    """
    Zestaw danych identyfikacyjnych oraz danych adresowych podatnika.

    Attributes:
        nip: Identyfikator podatkowy NIP
        nazwa: Imię i nazwisko lub nazwa
    """

    class Meta:
        name = "TPodmiot1"

    nip: str = field(
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        }
    )
    nazwa: str = field(
        metadata={
            "name": "Nazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 512,
        }
    )


class TrachunekWlasnyBanku(Enum):
    """
    Typy rachunków własnych.

    Attributes:
        VALUE_1: Rachunek banku lub rachunek spółdzielczej kasy
            oszczędnościowo-kredytowej służący do dokonywania rozliczeń
            z tytułu nabywanych przez ten bank lub tę kasę
            wierzytelności pieniężnych
        VALUE_2: Rachunek banku lub rachunek spółdzielczej kasy
            oszczędnościowo-kredytowej wykorzystywany przez ten bank lub
            tę kasę do pobrania należności od nabywcy towarów lub usług
            za dostawę towarów lub świadczenie usług, potwierdzone
            fakturą, i przekazania jej w całości albo części dostawcy
            towarów lub usługodawcy
        VALUE_3: Rachunek banku lub rachunek spółdzielczej kasy
            oszczędnościowo-kredytowej prowadzony przez ten bank lub tę
            kasę w ramach gospodarki własnej, niebędący rachunkiem
            rozliczeniowym
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3


class TrodzajFaktury(Enum):
    """
    Rodzaj faktury.

    Attributes:
        VAT: Faktura podstawowa
        KOR: Faktura korygująca
        ZAL: Faktura dokumentująca otrzymanie zapłaty lub jej części
            przed dokonaniem czynności oraz faktura wystawiona w związku
            z art. 106f ust. 4 ustawy (faktura zaliczkowa)
        ROZ: Faktura wystawiona w związku z art. 106f ust. 3 ustawy
        UPR: Faktura, o której mowa w art. 106e ust. 5 pkt 3 ustawy
        KOR_ZAL: Faktura korygująca fakturę dokumentującą otrzymanie
            zapłaty lub jej części przed dokonaniem czynności oraz
            fakturę wystawioną w związku z art. 106f ust. 4 ustawy
            (faktura korygująca fakturę zaliczkową)
        KOR_ROZ: Faktura korygująca fakturę wystawioną w związku z art.
            106f ust. 3 ustawy
    """

    VAT = "VAT"
    KOR = "KOR"
    ZAL = "ZAL"
    ROZ = "ROZ"
    UPR = "UPR"
    KOR_ZAL = "KOR_ZAL"
    KOR_ROZ = "KOR_ROZ"


class TrodzajTransportu(Enum):
    """
    Rodzaj transportu.

    Attributes:
        VALUE_1: Transport morski
        VALUE_2: Transport kolejowy
        VALUE_3: Transport drogowy
        VALUE_4: Transport lotniczy
        VALUE_5: Przesyłka pocztowa
        VALUE_7: Stałe instalacje przesyłowe
        VALUE_8: Żegluga śródlądowa
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_7 = 7
    VALUE_8 = 8


class TrolaPodmiotu3(Enum):
    """
    Rola podmiotu trzeciego.

    Attributes:
        VALUE_1: Faktor - w przypadku gdy na fakturze występują dane
            faktora
        VALUE_2: Odbiorca - w przypadku gdy na fakturze występują dane
            jednostek wewnętrznych, oddziałów, wyodrębnionych w ramach
            nabywcy, które same nie stanowią nabywcy w rozumieniu ustawy
        VALUE_3: Podmiot pierwotny - w przypadku gdy na fakturze
            występują dane podmiotu będącego w stosunku do podatnika
            podmiotem przejętym lub przekształconym, który dokonywał
            dostawy lub świadczył usługę. Z wyłączeniem przypadków, o
            których mowa w art. 106j ust.2 pkt 3 ustawy, gdy dane te
            wykazywane są w części Podmiot1K
        VALUE_4: Dodatkowy nabywca - w przypadku gdy na fakturze
            występują dane kolejnych (innych niż wymieniony w części
            Podmiot2) nabywców
        VALUE_5: Wystawca faktury - w przypadku gdy na fakturze
            występują dane podmiotu wystawiającego fakturę w imieniu
            podatnika. Nie dotyczy przypadku, gdy wystawcą faktury jest
            nabywca
        VALUE_6: Dokonujący płatności - w przypadku gdy na fakturze
            występują dane podmiotu regulującego zobowiązanie w miejsce
            nabywcy
        VALUE_7: Jednostka samorządu terytorialnego - wystawca
        VALUE_8: Jednostka samorządu terytorialnego - odbiorca
        VALUE_9: Członek grupy VAT - wystawca
        VALUE_10: Członek grupy VAT - odbiorca
        VALUE_11: Pracownik
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7
    VALUE_8 = 8
    VALUE_9 = 9
    VALUE_10 = 10
    VALUE_11 = 11


class TrolaPodmiotuUpowaznionego(Enum):
    """
    Rola podmiotu upoważnionego.

    Attributes:
        VALUE_1: Organ egzekucyjny - w przypadku, o którym mowa w art.
            106c pkt 1 ustawy
        VALUE_2: Komornik sądowy - w przypadku, o którym mowa w art.
            106c pkt 2 ustawy
        VALUE_3: Przedstawiciel podatkowy - w przypadku gdy na fakturze
            występują dane przedstawiciela podatkowego, o którym mowa w
            art. 18a - 18d ustawy
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3


class TstatusInfoPodatnika(Enum):
    """
    Status podatnika.

    Attributes:
        VALUE_1: Podatnik znajdujący się w stanie likwidacji
        VALUE_2: Podatnik, który jest w trakcie postępowania
            restrukturyzacyjnego
        VALUE_3: Podatnik znajdujący się w stanie upadłości
        VALUE_4: Przedsiębiorstwo w spadku
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4


class TstawkaPodatku(Enum):
    """
    Stawka podatku.

    Attributes:
        VALUE_23:
        VALUE_22:
        VALUE_8:
        VALUE_7:
        VALUE_5:
        VALUE_4:
        VALUE_3:
        VALUE_0_KR: Stawka 0% w przypadku sprzedaży towarów i
            świadczenia usług na terytorium kraju (z wyłączeniem WDT i
            eksportu)
        VALUE_0_WDT: Stawka 0% w przypadku wewnątrzwspólnotowej dostawy
            towarów (WDT)
        VALUE_0_EX: Stawka 0% w przypadku eksportu towarów
        ZW: zwolnione od podatku
        OO: odwrotne obciążenie
        NP_I: niepodlegające opodatkowaniu- dostawy towarów oraz
            świadczenia usług poza terytorium kraju, z wyłączeniem
            transakcji, o których mowa w art. 100 ust. 1 pkt 4 ustawy
            oraz OSS
        NP_II: niepodlegajace opodatkowaniu na terytorium kraju,
            świadczenie usług o których mowa w art. 100 ust. 1 pkt 4
            ustawy
    """

    VALUE_23 = "23"
    VALUE_22 = "22"
    VALUE_8 = "8"
    VALUE_7 = "7"
    VALUE_5 = "5"
    VALUE_4 = "4"
    VALUE_3 = "3"
    VALUE_0_KR = "0 KR"
    VALUE_0_WDT = "0 WDT"
    VALUE_0_EX = "0 EX"
    ZW = "zw"
    OO = "oo"
    NP_I = "np I"
    NP_II = "np II"


class TtypKorekty(Enum):
    """
    Typ skutku korekty w ewidencji dla podatku od towarów i usług.

    Attributes:
        VALUE_1: Korekta skutkująca w dacie ujęcia faktury pierwotnej
        VALUE_2: Korekta skutkująca w dacie wystawienia faktury
            korygującej
        VALUE_3: Korekta skutkująca w dacie innej, w tym gdy dla różnych
            pozycji faktury korygującej daty te są różne
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3


@dataclass(kw_only=True)
class FakturaFaAdnotacjeNoweSrodkiTransportu:
    """
    Attributes:
        p_22: Znacznik wewnątrzwspólnotowej dostawy nowych środków
            transportu
        p_42_5: Jeśli występuje obowiązek, o którym mowa w art. 42 ust.
            5 ustawy, należy podać wartość "1", w przeciwnym przypadku -
            wartość "2"
        nowy_srodek_transportu:
        p_22_n: Znacznik braku wewnątrzwspólnotowej dostawy nowych
            środków transportu
    """

    class Meta:
        global_type = False

    p_22: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_22",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_42_5: None | Twybor12 = field(
        default=None,
        metadata={
            "name": "P_42_5",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nowy_srodek_transportu: list[
        FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu
    ] = field(
        default_factory=list,
        metadata={
            "name": "NowySrodekTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 10000,
        },
    )
    p_22_n: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_22N",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaAdnotacjePmarzy:
    """
    Attributes:
        p_pmarzy: Znacznik wystąpienia procedur marży, o których mowa w
            art. 119 lub art. 120 ustawy
        p_pmarzy_2: Znacznik świadczenia usług turystyki, dla których
            podstawę opodatkowania stanowi marża, zgodnie z art. 119
            ust. 1 ustawy, a faktura dokumentująca świadczenie zawiera
            wyrazy "procedura marży dla biur podróży"
        p_pmarzy_3_1: Znacznik dostawy towarów używanych, dla których
            podstawę opodatkowania stanowi marża, zgodnie z art. 120
            ustawy, a faktura dokumentująca dostawę zawiera wyrazy
            "procedura marży - towary używane"
        p_pmarzy_3_2: Znacznik dostawy dzieł sztuki, dla których
            podstawę opodatkowania stanowi marża, zgodnie z art. 120
            ustawy, a faktura dokumentująca dostawę zawiera wyrazy
            "procedura marży - dzieła sztuki"
        p_pmarzy_3_3: Znacznik dostawy przedmiotów kolekcjonerskich i
            antyków, dla których podstawę opodatkowania stanowi marża,
            zgodnie z art. 120 ustawy, a faktura dokumentująca dostawę
            zawiera wyrazy "procedura marży - przedmioty kolekcjonerskie
            i antyki"
        p_pmarzy_n: Znacznik braku wystąpienia procedur marży, o których
            mowa w art. 119 lub art. 120 ustawy
    """

    class Meta:
        global_type = False

    p_pmarzy: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_PMarzy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_pmarzy_2: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_PMarzy_2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_pmarzy_3_1: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_PMarzy_3_1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_pmarzy_3_2: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_PMarzy_3_2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_pmarzy_3_3: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_PMarzy_3_3",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_pmarzy_n: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_PMarzyN",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaAdnotacjeZwolnienie:
    """
    Attributes:
        p_19: Znacznik dostawy towarów lub świadczenia usług zwolnionych
            od podatku na podstawie art. 43 ust. 1 ustawy, art. 113 ust.
            1 i 9 ustawy albo przepisów wydanych na podstawie art. 82
            ust. 3 ustawy lub na podstawie innych przepisów
        p_19_a: Jeśli pole P_19 równa się "1" - należy wskazać przepis
            ustawy albo aktu wydanego na podstawie ustawy, na podstawie
            którego podatnik stosuje zwolnienie od podatku
        p_19_b: Jeśli pole P_19 równa się "1" - należy wskazać przepis
            dyrektywy 2006/112/WE, który zwalnia od podatku taką dostawę
            towarów lub takie świadczenie usług
        p_19_c: Jeśli pole P_19 równa się "1" - należy wskazać inną
            podstawę prawną wskazującą na to, że dostawa towarów lub
            świadczenie usług korzysta ze zwolnienia od podatku
        p_19_n: Znacznik braku dostawy towarów lub świadczenia usług
            zwolnionych od podatku na podstawie art. 43 ust. 1 ustawy,
            art. 113 ust. 1 i 9 ustawy albo przepisów wydanych na
            podstawie art. 82 ust. 3 ustawy lub na podstawie innych
            przepisów
    """

    class Meta:
        global_type = False

    p_19: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_19",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_19_a: None | str = field(
        default=None,
        metadata={
            "name": "P_19A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_19_b: None | str = field(
        default=None,
        metadata={
            "name": "P_19B",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_19_c: None | str = field(
        default=None,
        metadata={
            "name": "P_19C",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_19_n: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_19N",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaDaneFaKorygowanej:
    """
    Attributes:
        data_wyst_fa_korygowanej: Data wystawienia faktury korygowanej
        nr_fa_korygowanej: Numer faktury korygowanej
        nr_kse_f: Znacznik numeru KSeF faktury korygowanej
        nr_kse_ffa_korygowanej: Numer identyfikujący fakturę korygowaną
            w KSeF
        nr_kse_fn: Znacznik faktury korygowanej wystawionej poza KSeF
    """

    class Meta:
        global_type = False

    data_wyst_fa_korygowanej: str = field(
        metadata={
            "name": "DataWystFaKorygowanej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    nr_fa_korygowanej: str = field(
        metadata={
            "name": "NrFaKorygowanej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )
    nr_kse_f: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "NrKSeF",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_kse_ffa_korygowanej: None | str = field(
        default=None,
        metadata={
            "name": "NrKSeFFaKorygowanej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"([1-9]((\d[1-9])|([1-9]\d))\d{7}|M\d{9}|[A-Z]{3}\d{7})-(20[2-9][0-9]|2[1-9][0-9]{2}|[3-9][0-9]{3})(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])-([0-9A-F]{6})-?([0-9A-F]{6})-([0-9A-F]{2})",
        },
    )
    nr_kse_fn: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "NrKSeFN",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaFaWiersz:
    """
    Attributes:
        nr_wiersza_fa: Kolejny numer wiersza faktury
        uu_id: Uniwersalny unikalny numer wiersza faktury
        p_6_a: Data dokonania lub zakończenia dostawy towarów lub
            wykonania usługi lub data otrzymania zapłaty, o której mowa
            w art. 106b ust. 1 pkt 4 ustawy, o ile taka data jest
            określona i różni się od daty wystawienia faktury. Pole
            wypełnia się w przypadku gdy dla poszczególnych pozycji
            faktury występują różne daty
        p_7: Nazwa (rodzaj) towaru lub usługi. Pole opcjonalne wyłącznie
            dla przypadku określonego w art 106j ust. 3 pkt 2 ustawy
            (faktura korygująca)
        indeks: Pole przeznaczone do wpisania wewnętrznego kodu towaru
            lub usługi nadanego przez podatnika albo dodatkowego opisu
        gtin: Globalny numer jednostki handlowej
        pkwi_u: Symbol Polskiej Klasyfikacji Wyrobów i Usług
        cn: Symbol Nomenklatury Scalonej
        pkob: Symbol Polskiej Klasyfikacji Obiektów Budowlanych
        p_8_a: Miara dostarczonych towarów lub zakres wykonanych usług.
            Pole opcjonalne dla przypadku określonego w art. 106e ust. 5
            pkt 3 ustawy
        p_8_b: Ilość (liczba) dostarczonych towarów lub zakres
            wykonanych usług. Pole opcjonalne dla przypadku określonego
            w art. 106e ust. 5 pkt 3 ustawy
        p_9_a: Cena jednostkowa towaru lub usługi bez kwoty podatku
            (cena jednostkowa netto). Pole opcjonalne dla przypadków
            określonych w art. 106e ust. 2 i 3 oraz ust. 5 pkt 3 ustawy
        p_9_b: Cena wraz z kwotą podatku (cena jednostkowa brutto), w
            przypadku zastosowania art. 106e ust. 7 i 8 ustawy
        p_10: Kwoty wszelkich opustów lub obniżek cen, w tym w formie
            rabatu z tytułu wcześniejszej zapłaty, o ile nie zostały one
            uwzględnione w cenie jednostkowej netto, a w przypadku
            stosowania art. 106e ust. 7 ustawy w cenie jednostkowej
            brutto. Pole opcjonalne dla przypadków określonych w art.
            106e ust. 2 i 3 oraz ust. 5 pkt 1 ustawy
        p_11: Wartość dostarczonych towarów lub wykonanych usług,
            objętych transakcją, bez kwoty podatku (wartość sprzedaży
            netto). Pole opcjonalne dla przypadków określonych w art.
            106e ust. 2 i 3 oraz ust. 5 pkt 3 ustawy
        p_11_a: Wartość sprzedaży brutto, w przypadku zastosowania art.
            106e ust. 7 i 8 ustawy
        p_11_vat: Kwota podatku w przypadku, o którym mowa w art. 106e
            ust. 10 ustawy
        p_12: Stawka podatku. Pole opcjonalne dla przypadków określonych
            w art. 106e ust. 2, 3, ust. 4 pkt 3 i ust. 5 pkt 3 ustawy
        p_12_xii: Stawka podatku od wartości dodanej w przypadku, o
            którym mowa w dziale XII w rozdziale 6a ustawy
        p_12_zal_15: Znacznik dla towaru lub usługi wymienionych w
            załączniku nr 15 do ustawy - wartość "1"
        kwota_akcyzy: Kwota podatku akcyzowego zawarta w cenie towaru
        gtu: Oznaczenie dotyczące dostawy towarów i świadczenia usług
        procedura: Oznaczenie dotyczące procedury
        kurs_waluty: Kurs waluty stosowany do wyliczenia kwoty podatku w
            przypadkach, o których mowa w dziale VI ustawy
        stan_przed: Znacznik stanu przed korektą w przypadku faktury
            korygującej lub faktury korygującej fakturę wystawioną w
            związku z art. 106f ust. 3 ustawy, w przypadku gdy korekta
            dotyczy danych wykazanych w pozycjach faktury i jest
            dokonywana w sposób polegający na wykazaniu danych przed
            korektą i po korekcie jako osobnych wierszy z odrębną
            numeracją oraz w przypadku potwierdzania braku zmiany
            wartości danej pozycji
    """

    class Meta:
        global_type = False

    nr_wiersza_fa: int = field(
        metadata={
            "name": "NrWierszaFa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_exclusive": 0,
            "total_digits": 14,
            "white_space": "collapse",
        }
    )
    uu_id: None | str = field(
        default=None,
        metadata={
            "name": "UU_ID",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    p_6_a: None | str = field(
        default=None,
        metadata={
            "name": "P_6A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        },
    )
    p_7: None | str = field(
        default=None,
        metadata={
            "name": "P_7",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )
    indeks: None | str = field(
        default=None,
        metadata={
            "name": "Indeks",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    gtin: None | str = field(
        default=None,
        metadata={
            "name": "GTIN",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 20,
        },
    )
    pkwi_u: None | str = field(
        default=None,
        metadata={
            "name": "PKWiU",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    cn: None | str = field(
        default=None,
        metadata={
            "name": "CN",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    pkob: None | str = field(
        default=None,
        metadata={
            "name": "PKOB",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    p_8_a: None | str = field(
        default=None,
        metadata={
            "name": "P_8A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_8_b: None | str = field(
        default=None,
        metadata={
            "name": "P_8B",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )
    p_9_a: None | str = field(
        default=None,
        metadata={
            "name": "P_9A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 8,
            "pattern": r"-?([1-9]\d{0,13}|0)(\.\d{1,8})?",
        },
    )
    p_9_b: None | str = field(
        default=None,
        metadata={
            "name": "P_9B",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 8,
            "pattern": r"-?([1-9]\d{0,13}|0)(\.\d{1,8})?",
        },
    )
    p_10: None | str = field(
        default=None,
        metadata={
            "name": "P_10",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 8,
            "pattern": r"-?([1-9]\d{0,13}|0)(\.\d{1,8})?",
        },
    )
    p_11: None | str = field(
        default=None,
        metadata={
            "name": "P_11",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_11_a: None | str = field(
        default=None,
        metadata={
            "name": "P_11A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_11_vat: None | str = field(
        default=None,
        metadata={
            "name": "P_11Vat",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_12: None | TstawkaPodatku = field(
        default=None,
        metadata={
            "name": "P_12",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_12_xii: None | Decimal = field(
        default=None,
        metadata={
            "name": "P_12_XII",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("100"),
            "total_digits": 9,
            "fraction_digits": 6,
            "white_space": "collapse",
        },
    )
    p_12_zal_15: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_12_Zal_15",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    kwota_akcyzy: None | str = field(
        default=None,
        metadata={
            "name": "KwotaAkcyzy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    gtu: None | Tgtu = field(
        default=None,
        metadata={
            "name": "GTU",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    procedura: None | ToznaczenieProcedury = field(
        default=None,
        metadata={
            "name": "Procedura",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    kurs_waluty: None | str = field(
        default=None,
        metadata={
            "name": "KursWaluty",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )
    stan_przed: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "StanPrzed",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaFakturaZaliczkowa:
    """
    Attributes:
        nr_kse_fzn: Znacznik faktury zaliczkowej wystawionej poza KSeF
        nr_fa_zaliczkowej: Numer faktury zaliczkowej wystawionej poza
            KSeF. Pole obowiązkowe dla faktury wystawianej po wydaniu
            towaru lub wykonaniu usługi, o której mowa w art. 106f ust.
            3 ustawy i ostatniej z faktur, o której mowa w art. 106f
            ust. 4 ustawy
        nr_kse_ffa_zaliczkowej: Numer identyfikujący fakturę zaliczkową
            w KSeF. Pole obowiązkowe w przypadku, gdy faktura zaliczkowa
            była wystawiona za pomocą KSeF
    """

    class Meta:
        global_type = False

    nr_kse_fzn: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "NrKSeFZN",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_fa_zaliczkowej: None | str = field(
        default=None,
        metadata={
            "name": "NrFaZaliczkowej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    nr_kse_ffa_zaliczkowej: None | str = field(
        default=None,
        metadata={
            "name": "NrKSeFFaZaliczkowej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"([1-9]((\d[1-9])|([1-9]\d))\d{7}|M\d{9}|[A-Z]{3}\d{7})-(20[2-9][0-9]|2[1-9][0-9]{2}|[3-9][0-9]{3})(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])-([0-9A-F]{6})-?([0-9A-F]{6})-([0-9A-F]{2})",
        },
    )


@dataclass(kw_only=True)
class FakturaFaPlatnoscTerminPlatnosci:
    """
    Attributes:
        termin: Termin płatności
        termin_opis: Opis terminu płatności
    """

    class Meta:
        global_type = False

    termin: None | str = field(
        default=None,
        metadata={
            "name": "Termin",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": "2016-07-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        },
    )
    termin_opis: None | FakturaFaPlatnoscTerminPlatnosciTerminOpis = field(
        default=None,
        metadata={
            "name": "TerminOpis",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaPlatnoscZaplataCzesciowa:
    """
    Attributes:
        kwota_zaplaty_czesciowej: Kwota zapłaty częściowej
        data_zaplaty_czesciowej: Data zapłaty częściowej, jeśli do
            wystawienia faktury płatność częściowa została dokonana
        forma_platnosci: Forma płatności
        platnosc_inna: Znacznik innej formy płatności: 1 - inna forma
            płatności
        opis_platnosci: Uszczegółowienie innej formy płatności
    """

    class Meta:
        global_type = False

    kwota_zaplaty_czesciowej: str = field(
        metadata={
            "name": "KwotaZaplatyCzesciowej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        }
    )
    data_zaplaty_czesciowej: str = field(
        metadata={
            "name": "DataZaplatyCzesciowej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2016-07-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    forma_platnosci: None | TformaPlatnosci = field(
        default=None,
        metadata={
            "name": "FormaPlatnosci",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    platnosc_inna: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "PlatnoscInna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    opis_platnosci: None | str = field(
        default=None,
        metadata={
            "name": "OpisPlatnosci",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaFaRozliczenie:
    """
    Attributes:
        obciazenia: Obciążenia
        suma_obciazen: Suma obciążeń
        odliczenia: Odliczenia
        suma_odliczen: Suma odliczeń
        do_zaplaty: Kwota należności do zapłaty równa polu P_15
            powiększonemu o Obciazenia i pomniejszonemu o Odliczenia
        do_rozliczenia: Kwota nadpłacona do rozliczenia/zwrotu
    """

    class Meta:
        global_type = False

    obciazenia: list[FakturaFaRozliczenieObciazenia] = field(
        default_factory=list,
        metadata={
            "name": "Obciazenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    suma_obciazen: None | str = field(
        default=None,
        metadata={
            "name": "SumaObciazen",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    odliczenia: list[FakturaFaRozliczenieOdliczenia] = field(
        default_factory=list,
        metadata={
            "name": "Odliczenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    suma_odliczen: None | str = field(
        default=None,
        metadata={
            "name": "SumaOdliczen",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    do_zaplaty: None | str = field(
        default=None,
        metadata={
            "name": "DoZaplaty",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    do_rozliczenia: None | str = field(
        default=None,
        metadata={
            "name": "DoRozliczenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )


@dataclass(kw_only=True)
class FakturaFaZamowienieZamowienieWiersz:
    """
    Attributes:
        nr_wiersza_zam: Kolejny numer wiersza zamówienia lub umowy
        uu_idz: Uniwersalny unikalny numer wiersza zamówienia lub umowy
        p_7_z: Nazwa (rodzaj) towaru lub usługi
        indeks_z: Pole przeznaczone do wpisania wewnętrznego kodu towaru
            lub usługi nadanego przez podatnika albo dodatkowego opisu
        gtinz: Globalny numer jednostki handlowej
        pkwi_uz: Symbol Polskiej Klasyfikacji Wyrobów i Usług
        cnz: Symbol Nomenklatury Scalonej
        pkobz: Symbol Polskiej Klasyfikacji Obiektów Budowlanych
        p_8_az: Miara zamówionego towaru lub zakres usługi
        p_8_bz: Ilość zamówionego towaru lub zakres usługi
        p_9_az: Cena jednostkowa netto
        p_11_netto_z: Wartość zamówionego towaru lub usługi bez kwoty
            podatku
        p_11_vat_z: Kwota podatku od zamówionego towaru lub usługi
        p_12_z: Stawka podatku
        p_12_z_xii: Stawka podatku od wartości dodanej w przypadku, o
            którym mowa w dziale XII w rozdziale 6a ustawy
        p_12_z_zal_15: Znacznik dla towaru lub usługi wymienionych w
            załączniku nr 15 do ustawy - wartość "1"
        gtuz: Oznaczenie dotyczące dostawy towarów i świadczenia usług
        procedura_z: Oznaczenia dotyczące procedur
        kwota_akcyzy_z: Kwota podatku akcyzowego zawarta w cenie towaru
        stan_przed_z: Znacznik stanu przed korektą w przypadku faktury
            korygującej fakturę dokumentującą otrzymanie zapłaty lub jej
            części przed dokonaniem czynności oraz fakturę wystawioną w
            związku z art. 106f ust. 4 ustawy (faktura korygująca
            fakturę zaliczkową), w przypadku gdy korekta dotyczy danych
            wykazanych w pozycjach zamówienia i jest dokonywana w sposób
            polegający na wykazaniu danych przed korektą i po korekcie
            jako osobnych wierszy z odrębną numeracją oraz w przypadku
            potwierdzania braku zmiany wartości danej pozycji
    """

    class Meta:
        global_type = False

    nr_wiersza_zam: int = field(
        metadata={
            "name": "NrWierszaZam",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_exclusive": 0,
            "total_digits": 14,
            "white_space": "collapse",
        }
    )
    uu_idz: None | str = field(
        default=None,
        metadata={
            "name": "UU_IDZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    p_7_z: None | str = field(
        default=None,
        metadata={
            "name": "P_7Z",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )
    indeks_z: None | str = field(
        default=None,
        metadata={
            "name": "IndeksZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    gtinz: None | str = field(
        default=None,
        metadata={
            "name": "GTINZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 20,
        },
    )
    pkwi_uz: None | str = field(
        default=None,
        metadata={
            "name": "PKWiUZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    cnz: None | str = field(
        default=None,
        metadata={
            "name": "CNZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    pkobz: None | str = field(
        default=None,
        metadata={
            "name": "PKOBZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    p_8_az: None | str = field(
        default=None,
        metadata={
            "name": "P_8AZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_8_bz: None | str = field(
        default=None,
        metadata={
            "name": "P_8BZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )
    p_9_az: None | str = field(
        default=None,
        metadata={
            "name": "P_9AZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 8,
            "pattern": r"-?([1-9]\d{0,13}|0)(\.\d{1,8})?",
        },
    )
    p_11_netto_z: None | str = field(
        default=None,
        metadata={
            "name": "P_11NettoZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_11_vat_z: None | str = field(
        default=None,
        metadata={
            "name": "P_11VatZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_12_z: None | TstawkaPodatku = field(
        default=None,
        metadata={
            "name": "P_12Z",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_12_z_xii: None | Decimal = field(
        default=None,
        metadata={
            "name": "P_12Z_XII",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("100"),
            "total_digits": 9,
            "fraction_digits": 6,
            "white_space": "collapse",
        },
    )
    p_12_z_zal_15: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "P_12Z_Zal_15",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    gtuz: None | Tgtu = field(
        default=None,
        metadata={
            "name": "GTUZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    procedura_z: None | ToznaczenieProceduryZ = field(
        default=None,
        metadata={
            "name": "ProceduraZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    kwota_akcyzy_z: None | str = field(
        default=None,
        metadata={
            "name": "KwotaAkcyzyZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    stan_przed_z: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "StanPrzedZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaStopka:
    """
    Attributes:
        informacje: Pozostałe dane
        rejestry: Numery podmiotu lub grupy podmiotów w innych
            rejestrach i bazach danych
    """

    class Meta:
        global_type = False

    informacje: list[FakturaStopkaInformacje] = field(
        default_factory=list,
        metadata={
            "name": "Informacje",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 3,
        },
    )
    rejestry: list[FakturaStopkaRejestry] = field(
        default_factory=list,
        metadata={
            "name": "Rejestry",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabelaTnaglowekKol:
    """
    Attributes:
        nkom: Zawartość pola
        typ:
    """

    class Meta:
        global_type = False

    nkom: FakturaZalacznikBlokDanychTabelaTnaglowekKolNkom = field(
        metadata={
            "name": "NKom",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    typ: FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp = field(
        metadata={
            "name": "Typ",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class Tadres:
    """
    Informacje opisujące adres.

    Attributes:
        kod_kraju: Kod Kraju [Country Code]
        adres_l1: Adres [Address]
        adres_l2: Adres [Address]
        gln: Globalny Numer Lokalizacyjny [Global Location Number]
    """

    class Meta:
        name = "TAdres"

    kod_kraju: TkodKraju = field(
        metadata={
            "name": "KodKraju",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres_l1: str = field(
        metadata={
            "name": "AdresL1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 512,
        }
    )
    adres_l2: None | str = field(
        default=None,
        metadata={
            "name": "AdresL2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )
    gln: None | str = field(
        default=None,
        metadata={
            "name": "GLN",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 13,
        },
    )


@dataclass(kw_only=True)
class TnaglowekKodFormularza:
    class Meta:
        global_type = False

    value: TkodFormularza = field(
        metadata={
            "required": True,
        }
    )
    kod_systemowy: str = field(
        init=False,
        default="FA (3)",
        metadata={
            "name": "kodSystemowy",
            "type": "Attribute",
            "required": True,
        },
    )
    wersja_schemy: str = field(
        init=False,
        default="1-0E",
        metadata={
            "name": "wersjaSchemy",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class Tpodmiot2:
    """
    Zestaw danych identyfikacyjnych oraz danych adresowych nabywcy.

    Attributes:
        nip: Identyfikator podatkowy NIP
        kod_ue: Kod (prefiks) nabywcy VAT UE, o którym mowa w art. 106e
            ust. 1 pkt 24 ustawy oraz w przypadku, o którym mowa w art.
            136 ust. 1 pkt 4 ustawy
        nr_vat_ue: Numer Identyfikacyjny VAT kontrahenta UE
        kod_kraju: Kod kraju nadania identyfikatora podatkowego
        nr_id: Identyfikator podatkowy inny
        brak_id: Podmiot nie posiada identyfikatora podatkowego lub
            identyfikator nie występuje na fakturze: 1- tak
        nazwa: Imię i nazwisko lub nazwa
    """

    class Meta:
        name = "TPodmiot2"

    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )
    kod_ue: None | TkodyKrajowUe = field(
        default=None,
        metadata={
            "name": "KodUE",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_vat_ue: None | str = field(
        default=None,
        metadata={
            "name": "NrVatUE",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"(\d|[A-Z]|\+|\*){1,12}",
        },
    )
    kod_kraju: None | TkodKraju = field(
        default=None,
        metadata={
            "name": "KodKraju",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_id: None | str = field(
        default=None,
        metadata={
            "name": "NrID",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
            "white_space": "replace",
        },
    )
    brak_id: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "BrakID",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nazwa: None | str = field(
        default=None,
        metadata={
            "name": "Nazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )


@dataclass(kw_only=True)
class Tpodmiot3:
    """
    Zestaw danych identyfikacyjnych oraz danych adresowych podmiotów
    trzecich.

    Attributes:
        nip: Identyfikator podatkowy NIP
        idwew: Identyfikator wewnętrzny z NIP
        kod_ue: Kod (prefiks) nabywcy VAT UE, o którym mowa w art. 106e
            ust. 1 pkt 24 ustawy oraz w przypadku, o którym mowa w art.
            136 ust. 1 pkt 4 ustawy
        nr_vat_ue: Numer Identyfikacyjny VAT kontrahenta UE
        kod_kraju: Kod kraju nadania identyfikatora podatkowego
        nr_id: Identyfikator podatkowy inny
        brak_id: Podmiot nie posiada identyfikatora podatkowego lub
            identyfikator nie występuje na fakturze: 1- tak
        nazwa: Imię i nazwisko lub nazwa
    """

    class Meta:
        name = "TPodmiot3"

    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )
    idwew: None | str = field(
        default=None,
        metadata={
            "name": "IDWew",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 20,
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}-\d{5}",
        },
    )
    kod_ue: None | TkodyKrajowUe = field(
        default=None,
        metadata={
            "name": "KodUE",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_vat_ue: None | str = field(
        default=None,
        metadata={
            "name": "NrVatUE",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"(\d|[A-Z]|\+|\*){1,12}",
        },
    )
    kod_kraju: None | TkodKraju = field(
        default=None,
        metadata={
            "name": "KodKraju",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_id: None | str = field(
        default=None,
        metadata={
            "name": "NrID",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
            "white_space": "replace",
        },
    )
    brak_id: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "BrakID",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nazwa: None | str = field(
        default=None,
        metadata={
            "name": "Nazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )


@dataclass(kw_only=True)
class TrachunekBankowy:
    """
    Informacje o rachunku.

    Attributes:
        nr_rb: Pełny numer rachunku
        swift: Kod SWIFT
        rachunek_wlasny_banku: Rachunek własny
        nazwa_banku: Nazwa
        opis_rachunku: Opis rachunku
    """

    class Meta:
        name = "TRachunekBankowy"

    nr_rb: str = field(
        metadata={
            "name": "NrRB",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 10,
            "max_length": 34,
        }
    )
    swift: None | str = field(
        default=None,
        metadata={
            "name": "SWIFT",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "pattern": r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3}){0,1}",
        },
    )
    rachunek_wlasny_banku: None | TrachunekWlasnyBanku = field(
        default=None,
        metadata={
            "name": "RachunekWlasnyBanku",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nazwa_banku: None | str = field(
        default=None,
        metadata={
            "name": "NazwaBanku",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    opis_rachunku: None | str = field(
        default=None,
        metadata={
            "name": "OpisRachunku",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaFaAdnotacje:
    """
    Attributes:
        p_16: W przypadku dostawy towarów lub świadczenia usług, w
            odniesieniu do których obowiązek podatkowy powstaje zgodnie
            z art. 19a ust. 5 pkt 1 lub art. 21 ust. 1 ustawy - wyrazy
            "metoda kasowa"; należy podać wartość "1", w przeciwnym
            przypadku - wartość "2"
        p_17: W przypadku faktur, o których mowa w art. 106d ust. 1
            ustawy - wyraz "samofakturowanie"; należy podać wartość "1",
            w przeciwnym przypadku - wartość "2"
        p_18: W przypadku dostawy towarów lub wykonania usługi, dla
            których obowiązanym do rozliczenia podatku od wartości
            dodanej lub podatku o podobnym charakterze jest nabywca
            towaru lub usługi - wyrazy "odwrotne obciążenie"; należy
            podać wartość "1", w przeciwnym przypadku - wartość "2"
        p_18_a: W przypadku faktur, w których kwota należności ogółem
            przekracza kwotę 15 000 zł lub jej równowartość wyrażoną w
            walucie obcej, obejmujących dokonaną na rzecz podatnika
            dostawę towarów lub świadczenie usług, o których mowa w
            załączniku nr 15 do ustawy - wyrazy "mechanizm podzielonej
            płatności", przy czym do przeliczania na złote kwot
            wyrażonych w walucie obcej stosuje się zasady przeliczania
            kwot stosowane w celu określenia podstawy opodatkowania;
            należy podać wartość "1", w przeciwnym przypadku - wartość
            "2"
        zwolnienie:
        nowe_srodki_transportu:
        p_23: W przypadku faktur wystawianych w procedurze uproszczonej
            przez drugiego w kolejności podatnika, o którym mowa w art.
            135 ust. 1 pkt 4 lit. b i c oraz ust. 2 ustawy, zawierającej
            adnotację, o której mowa w art. 136 ust. 1 pkt 1 ustawy i
            stwierdzenie, o którym mowa w art. 136 ust. 1 pkt 2 ustawy,
            należy podać wartość "1", w przeciwnym przypadku - wartość
            "2"
        pmarzy:
    """

    class Meta:
        global_type = False

    p_16: Twybor12 = field(
        metadata={
            "name": "P_16",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    p_17: Twybor12 = field(
        metadata={
            "name": "P_17",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    p_18: Twybor12 = field(
        metadata={
            "name": "P_18",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    p_18_a: Twybor12 = field(
        metadata={
            "name": "P_18A",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    zwolnienie: FakturaFaAdnotacjeZwolnienie = field(
        metadata={
            "name": "Zwolnienie",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    nowe_srodki_transportu: FakturaFaAdnotacjeNoweSrodkiTransportu = field(
        metadata={
            "name": "NoweSrodkiTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    p_23: Twybor12 = field(
        metadata={
            "name": "P_23",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    pmarzy: FakturaFaAdnotacjePmarzy = field(
        metadata={
            "name": "PMarzy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class FakturaFaPlatnosc:
    """
    Attributes:
        zaplacono: Znacznik informujący, że należność wynikająca z
            faktury została zapłacona: 1 - zapłacono
        data_zaplaty: Data zapłaty, jeśli do wystawienia faktury
            płatność została dokonana
        znacznik_zaplaty_czesciowej: Znacznik informujący, że należność
            wynikająca z faktury została zapłacona w części lub w
            całości:                                 1 - zapłacono w
            części;                           2 - zapłacono w całości,
            jeśli należność wynikająca z faktury została zapłacona w
            dwóch lub więcej częściach, a ostatnia płatność jest
            płatnością końcową
        zaplata_czesciowa: Dane zapłat częściowych
        termin_platnosci:
        forma_platnosci: Forma płatności
        platnosc_inna: Znacznik innej formy płatności: 1 - inna forma
            płatności
        opis_platnosci: Uszczegółowienie innej formy płatności
        rachunek_bankowy: Numer rachunku
        rachunek_bankowy_faktora: Rachunek faktora
        skonto: Skonto
        link_do_platnosci: Link do płatności bezgotówkowej
        ipkse_f: Identyfikator płatności Krajowego Systemu e-Faktur
    """

    class Meta:
        global_type = False

    zaplacono: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "Zaplacono",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    data_zaplaty: None | str = field(
        default=None,
        metadata={
            "name": "DataZaplaty",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": "2016-07-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        },
    )
    znacznik_zaplaty_czesciowej: None | Twybor12 = field(
        default=None,
        metadata={
            "name": "ZnacznikZaplatyCzesciowej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    zaplata_czesciowa: list[FakturaFaPlatnoscZaplataCzesciowa] = field(
        default_factory=list,
        metadata={
            "name": "ZaplataCzesciowa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    termin_platnosci: list[FakturaFaPlatnoscTerminPlatnosci] = field(
        default_factory=list,
        metadata={
            "name": "TerminPlatnosci",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    forma_platnosci: None | TformaPlatnosci = field(
        default=None,
        metadata={
            "name": "FormaPlatnosci",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    platnosc_inna: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "PlatnoscInna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    opis_platnosci: None | str = field(
        default=None,
        metadata={
            "name": "OpisPlatnosci",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    rachunek_bankowy: list[TrachunekBankowy] = field(
        default_factory=list,
        metadata={
            "name": "RachunekBankowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    rachunek_bankowy_faktora: list[TrachunekBankowy] = field(
        default_factory=list,
        metadata={
            "name": "RachunekBankowyFaktora",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 20,
        },
    )
    skonto: None | FakturaFaPlatnoscSkonto = field(
        default=None,
        metadata={
            "name": "Skonto",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    link_do_platnosci: None | str = field(
        default=None,
        metadata={
            "name": "LinkDoPlatnosci",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
            "pattern": r"(https?)://([a-zA-Z0-9][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}(:[0-9]{1,5})?(/[^\s?#]*)?\?([^#\s]*&)?IPKSeF=[0-9]{3}[a-zA-Z0-9]{10}(&[^#\s]*)?(#.*)?",
        },
    )
    ipkse_f: None | str = field(
        default=None,
        metadata={
            "name": "IPKSeF",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 13,
            "pattern": r"[0-9]{3}[a-zA-Z0-9]{10}",
        },
    )


@dataclass(kw_only=True)
class FakturaFaPodmiot1K:
    """
    Attributes:
        prefiks_podatnika: Kod (prefiks) podatnika VAT UE dla przypadków
            określonych w art. 97 ust. 10 pkt 2 i 3 ustawy oraz w
            przypadku, o którym mowa w art. 136 ust. 1 pkt 3 ustawy
        dane_identyfikacyjne: Dane identyfikujące podatnika
        adres: Adres podatnika
    """

    class Meta:
        global_type = False

    prefiks_podatnika: None | TkodyKrajowUe = field(
        default=None,
        metadata={
            "name": "PrefiksPodatnika",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dane_identyfikacyjne: Tpodmiot1 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres: Tadres = field(
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class FakturaFaPodmiot2K:
    """
    Attributes:
        dane_identyfikacyjne: Dane identyfikujące nabywcę
        adres: Adres nabywcy. Pola opcjonalne dla przypadków określonych
            w art. 106e ust. 5 pkt 3 ustawy
        idnabywcy: Unikalny klucz powiązania danych nabywcy na fakturach
            korygujących, w przypadku gdy dane nabywcy na fakturze
            korygującej zmieniły się w stosunku do danych na fakturze
            korygowanej
    """

    class Meta:
        global_type = False

    dane_identyfikacyjne: Tpodmiot2 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres: None | Tadres = field(
        default=None,
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    idnabywcy: None | str = field(
        default=None,
        metadata={
            "name": "IDNabywcy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 32,
        },
    )


@dataclass(kw_only=True)
class FakturaFaWarunkiTransakcjiTransportPrzewoznik:
    """
    Attributes:
        dane_identyfikacyjne: Dane identyfikacyjne przewoźnika
        adres_przewoznika: Adres przewoźnika
    """

    class Meta:
        global_type = False

    dane_identyfikacyjne: Tpodmiot2 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres_przewoznika: Tadres = field(
        metadata={
            "name": "AdresPrzewoznika",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class FakturaFaZamowienie:
    """
    Attributes:
        wartosc_zamowienia: Wartość zamówienia lub umowy z
            uwzględnieniem kwoty podatku
        zamowienie_wiersz: Szczegółowe pozycje zamówienia lub umowy w
            walucie, w której wystawiono fakturę zaliczkową
    """

    class Meta:
        global_type = False

    wartosc_zamowienia: str = field(
        metadata={
            "name": "WartoscZamowienia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        }
    )
    zamowienie_wiersz: list[FakturaFaZamowienieZamowienieWiersz] = field(
        default_factory=list,
        metadata={
            "name": "ZamowienieWiersz",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 10000,
        },
    )


@dataclass(kw_only=True)
class FakturaPodmiot1AdresKoresp(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False


@dataclass(kw_only=True)
class FakturaPodmiot2:
    """
    Attributes:
        nr_eori: Numer EORI nabywcy towarów
        dane_identyfikacyjne: Dane identyfikujące nabywcę
        adres: Adres nabywcy. Pola opcjonalne dla przypadków określonych
            w art. 106e ust. 5 pkt 3 ustawy
        adres_koresp: Adres korespondencyjny nabywcy
        dane_kontaktowe: Dane kontaktowe nabywcy
        nr_klienta: Numer klienta dla przypadków, w których nabywca
            posługuje się nim w umowie lub zamówieniu
        idnabywcy: Unikalny klucz powiązania danych nabywcy na fakturach
            korygujących, w przypadku gdy dane nabywcy na fakturze
            korygującej zmieniły się w stosunku do danych na fakturze
            korygowanej
        jst: Znacznik jednostki podrzędnej JST. Wartość "1" oznacza, że
            faktura dotyczy jednostki podrzędnej JST. W takim przypadku,
            aby udostępnić fakturę jednostce podrzędnej JST, należy
            wypełnić sekcję Podmiot3, w szczególności podać NIP lub ID-
            Wew i określić rolę jako 8. Wartość "2" oznacza, że faktura
            nie dotyczy jednostki podrzędnej JST
        gv: Znacznik członka grupy VAT.
            Wartość "1" oznacza, że faktura dotyczy członka grupy VAT. W
            takim przypadku, aby udostępnić fakturę członkowi grupy VAT,
            należy wypełnić sekcję Podmiot3, w szczególności podać NIP
            lub ID-Wew i określić rolę jako 10. Wartość "2" oznacza, że
            faktura nie dotyczy członka grupy VAT
    """

    class Meta:
        global_type = False

    nr_eori: None | str = field(
        default=None,
        metadata={
            "name": "NrEORI",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    dane_identyfikacyjne: Tpodmiot2 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres: None | Tadres = field(
        default=None,
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    adres_koresp: None | Tadres = field(
        default=None,
        metadata={
            "name": "AdresKoresp",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dane_kontaktowe: list[FakturaPodmiot2DaneKontaktowe] = field(
        default_factory=list,
        metadata={
            "name": "DaneKontaktowe",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 3,
        },
    )
    nr_klienta: None | str = field(
        default=None,
        metadata={
            "name": "NrKlienta",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    idnabywcy: None | str = field(
        default=None,
        metadata={
            "name": "IDNabywcy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 32,
        },
    )
    jst: FakturaPodmiot2Jst = field(
        metadata={
            "name": "JST",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    gv: FakturaPodmiot2Gv = field(
        metadata={
            "name": "GV",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class FakturaPodmiot3:
    """
    Attributes:
        idnabywcy: Unikalny klucz powiązania danych nabywcy na fakturach
            korygujących, w przypadku gdy dane nabywcy na fakturze
            korygującej zmieniły się w stosunku do danych na fakturze
            korygowanej
        nr_eori: Numer EORI podmiotu trzeciego
        dane_identyfikacyjne: Dane identyfikujące podmiot trzeci
        adres: Adres podmiotu trzeciego
        adres_koresp: Adres korespondencyjny podmiotu trzeciego
        dane_kontaktowe: Dane kontaktowe podmiotu trzeciego
        rola: Rola podmiotu
        rola_inna: Znacznik innego podmiotu: 1 - Inny podmiot
        opis_roli: Opis roli podmiotu - w przypadku wyboru roli jako
            Inny podmiot
        udzial: Udział - procentowy udział dodatkowego nabywcy. Różnica
            pomiędzy wartością 100% a sumą udziałów dodatkowych nabywców
            jest udziałem nabywcy wymienionego w części Podmiot2. W
            przypadku niewypełnienia pola przyjmuje się, że udziały
            występujących na fakturze nabywców są równe
        nr_klienta: Numer klienta dla przypadków, w których podmiot
            wymieniony jako podmiot trzeci posługuje się nim w umowie
            lub zamówieniu
    """

    class Meta:
        global_type = False

    idnabywcy: None | str = field(
        default=None,
        metadata={
            "name": "IDNabywcy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 32,
        },
    )
    nr_eori: None | str = field(
        default=None,
        metadata={
            "name": "NrEORI",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    dane_identyfikacyjne: Tpodmiot3 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres: None | Tadres = field(
        default=None,
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    adres_koresp: None | Tadres = field(
        default=None,
        metadata={
            "name": "AdresKoresp",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dane_kontaktowe: list[FakturaPodmiot3DaneKontaktowe] = field(
        default_factory=list,
        metadata={
            "name": "DaneKontaktowe",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 3,
        },
    )
    rola: None | TrolaPodmiotu3 = field(
        default=None,
        metadata={
            "name": "Rola",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    rola_inna: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "RolaInna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    opis_roli: None | str = field(
        default=None,
        metadata={
            "name": "OpisRoli",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    udzial: None | Decimal = field(
        default=None,
        metadata={
            "name": "Udzial",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("100"),
            "total_digits": 9,
            "fraction_digits": 6,
            "white_space": "collapse",
        },
    )
    nr_klienta: None | str = field(
        default=None,
        metadata={
            "name": "NrKlienta",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaPodmiotUpowazniony:
    """
    Attributes:
        nr_eori: Numer EORI podmiotu upoważnionego
        dane_identyfikacyjne: Dane identyfikujące podmiotu upoważnionego
        adres: Adres podmiotu upoważnionego
        adres_koresp: Adres korespondencyjny podmiotu upoważnionego
        dane_kontaktowe: Dane kontaktowe podmiotu upoważnionego
        rola_pu: Rola podmiotu upoważnionego
    """

    class Meta:
        global_type = False

    nr_eori: None | str = field(
        default=None,
        metadata={
            "name": "NrEORI",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    dane_identyfikacyjne: Tpodmiot1 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres: Tadres = field(
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres_koresp: None | Tadres = field(
        default=None,
        metadata={
            "name": "AdresKoresp",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dane_kontaktowe: list[FakturaPodmiotUpowaznionyDaneKontaktowe] = field(
        default_factory=list,
        metadata={
            "name": "DaneKontaktowe",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 3,
        },
    )
    rola_pu: TrolaPodmiotuUpowaznionego = field(
        metadata={
            "name": "RolaPU",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabelaTnaglowek:
    class Meta:
        global_type = False

    kol: list[FakturaZalacznikBlokDanychTabelaTnaglowekKol] = field(
        default_factory=list,
        metadata={
            "name": "Kol",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 20,
        },
    )


@dataclass(kw_only=True)
class Tnaglowek:
    """
    Nagłówek.

    Attributes:
        kod_formularza:
        wariant_formularza:
        data_wytworzenia_fa: Data i czas wytworzenia faktury
        system_info: Nazwa systemu teleinformatycznego, z którego
            korzysta podatnik
    """

    class Meta:
        name = "TNaglowek"

    kod_formularza: TnaglowekKodFormularza = field(
        metadata={
            "name": "KodFormularza",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    wariant_formularza: TnaglowekWariantFormularza = field(
        metadata={
            "name": "WariantFormularza",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    data_wytworzenia_fa: XmlDateTime = field(
        metadata={
            "name": "DataWytworzeniaFa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": XmlDateTime(2025, 9, 1, 0, 0, 0, 0, 0),
            "max_inclusive": XmlDateTime(2050, 1, 1, 23, 59, 59, 0, 0),
            "white_space": "collapse",
        }
    )
    system_info: None | str = field(
        default=None,
        metadata={
            "name": "SystemInfo",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )


@dataclass(kw_only=True)
class FakturaFaWarunkiTransakcjiTransport:
    """
    Attributes:
        rodzaj_transportu: Rodzaj zastosowanego transportu w przypadku
            dokonanej dostawy towarów
        transport_inny: Znacznik innego rodzaju transportu: 1 - inny
            rodzaj transportu
        opis_innego_transportu: Opis innego rodzaju transportu
        przewoznik:
        nr_zlecenia_transportu: Numer zlecenia transportu
        opis_ladunku: Rodzaj ładunku
        ladunek_inny: Znacznik innego ładunku: 1 - inny ładunek
        opis_innego_ladunku: Opis innego ładunku, w tym ładunek mieszany
        jednostka_opakowania: Jednostka opakowania
        data_godz_rozp_transportu: Data i godzina rozpoczęcia transportu
        data_godz_zak_transportu: Data i godzina zakończenia transportu
        wysylka_z: Adres miejsca wysyłki
        wysylka_przez: Adres pośredni wysyłki
        wysylka_do: Adres miejsca docelowego, do którego został zlecony
            transport
    """

    class Meta:
        global_type = False

    rodzaj_transportu: None | TrodzajTransportu = field(
        default=None,
        metadata={
            "name": "RodzajTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    transport_inny: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "TransportInny",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    opis_innego_transportu: None | str = field(
        default=None,
        metadata={
            "name": "OpisInnegoTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    przewoznik: None | FakturaFaWarunkiTransakcjiTransportPrzewoznik = field(
        default=None,
        metadata={
            "name": "Przewoznik",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_zlecenia_transportu: None | str = field(
        default=None,
        metadata={
            "name": "NrZleceniaTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    opis_ladunku: None | Tladunek = field(
        default=None,
        metadata={
            "name": "OpisLadunku",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    ladunek_inny: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "LadunekInny",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    opis_innego_ladunku: None | str = field(
        default=None,
        metadata={
            "name": "OpisInnegoLadunku",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 50,
        },
    )
    jednostka_opakowania: None | str = field(
        default=None,
        metadata={
            "name": "JednostkaOpakowania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    data_godz_rozp_transportu: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "DataGodzRozpTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": XmlDateTime(2021, 10, 1, 0, 0, 0, 0, 0),
            "max_inclusive": XmlDateTime(2050, 1, 1, 23, 59, 59, 0, 0),
            "white_space": "collapse",
        },
    )
    data_godz_zak_transportu: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "DataGodzZakTransportu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": XmlDateTime(2021, 10, 1, 0, 0, 0, 0, 0),
            "max_inclusive": XmlDateTime(2050, 1, 1, 23, 59, 59, 0, 0),
            "white_space": "collapse",
        },
    )
    wysylka_z: None | Tadres = field(
        default=None,
        metadata={
            "name": "WysylkaZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    wysylka_przez: list[Tadres] = field(
        default_factory=list,
        metadata={
            "name": "WysylkaPrzez",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 20,
        },
    )
    wysylka_do: None | Tadres = field(
        default=None,
        metadata={
            "name": "WysylkaDo",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaPodmiot1:
    """
    Attributes:
        prefiks_podatnika: Kod (prefiks) podatnika VAT UE dla przypadków
            określonych w art. 97 ust. 10 pkt 2 i 3 ustawy oraz w
            przypadku, o którym mowa w art. 136 ust. 1 pkt 3 ustawy
        nr_eori: Numer EORI podatnika (sprzedawcy)
        dane_identyfikacyjne: Dane identyfikujące podatnika
        adres: Adres podatnika
        adres_koresp: Adres korespondencyjny podatnika
        dane_kontaktowe: Dane kontaktowe podatnika
        status_info_podatnika: Status podatnika
    """

    class Meta:
        global_type = False

    prefiks_podatnika: None | TkodyKrajowUe = field(
        default=None,
        metadata={
            "name": "PrefiksPodatnika",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    nr_eori: None | str = field(
        default=None,
        metadata={
            "name": "NrEORI",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    dane_identyfikacyjne: Tpodmiot1 = field(
        metadata={
            "name": "DaneIdentyfikacyjne",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres: Tadres = field(
        metadata={
            "name": "Adres",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    adres_koresp: None | FakturaPodmiot1AdresKoresp = field(
        default=None,
        metadata={
            "name": "AdresKoresp",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dane_kontaktowe: list[FakturaPodmiot1DaneKontaktowe] = field(
        default_factory=list,
        metadata={
            "name": "DaneKontaktowe",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 3,
        },
    )
    status_info_podatnika: None | TstatusInfoPodatnika = field(
        default=None,
        metadata={
            "name": "StatusInfoPodatnika",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanychTabela:
    """
    Attributes:
        tmeta_dane: Dane opisowe dotyczące tabeli
        opis: Opis
        tnaglowek: Nagłówek tabeli
        wiersz: Wiersze tabeli
        suma: Podsumowania tabeli
    """

    class Meta:
        global_type = False

    tmeta_dane: list[FakturaZalacznikBlokDanychTabelaTmetaDane] = field(
        default_factory=list,
        metadata={
            "name": "TMetaDane",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 1000,
        },
    )
    opis: None | str = field(
        default=None,
        metadata={
            "name": "Opis",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )
    tnaglowek: FakturaZalacznikBlokDanychTabelaTnaglowek = field(
        metadata={
            "name": "TNaglowek",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    wiersz: list[FakturaZalacznikBlokDanychTabelaWiersz] = field(
        default_factory=list,
        metadata={
            "name": "Wiersz",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )
    suma: None | FakturaZalacznikBlokDanychTabelaSuma = field(
        default=None,
        metadata={
            "name": "Suma",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaFaWarunkiTransakcji:
    """
    Attributes:
        umowy:
        zamowienia:
        nr_partii_towaru: Numery partii towaru
        warunki_dostawy: Warunki dostawy towarów - w przypadku istnienia
            pomiędzy stronami transakcji, umowy określającej warunki
            dostawy tzw. Incoterms
        kurs_umowny: Kurs umowny - w przypadkach, gdy na fakturze
            znajduje się informacja o kursie, po którym zostały
            przeliczone kwoty wykazane na fakturze w złotych. Nie
            dotyczy przypadków, o których mowa w dziale VI ustawy
        waluta_umowna: Waluta umowna - kod waluty (ISO-4217) w
            przypadkach gdy na fakturze znajduje się informacja o
            kursie, po którym zostały przeliczone kwoty wykazane na
            fakturze w złotych. Nie dotyczy przypadków, o których mowa w
            dziale VI ustawy
        transport:
        podmiot_posredniczacy: Wartość "1" oznacza dostawę dokonaną
            przez podmiot, o którym mowa w art. 22 ust. 2d ustawy. Pole
            dotyczy przypadku, w którym podmiot uczestniczy w transakcji
            łańcuchowej innej niż procedura trójstronna uproszczona, o
            której mowa w art. 135 ust. 1 pkt 4 ustawy
    """

    class Meta:
        global_type = False

    umowy: list[FakturaFaWarunkiTransakcjiUmowy] = field(
        default_factory=list,
        metadata={
            "name": "Umowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    zamowienia: list[FakturaFaWarunkiTransakcjiZamowienia] = field(
        default_factory=list,
        metadata={
            "name": "Zamowienia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    nr_partii_towaru: list[str] = field(
        default_factory=list,
        metadata={
            "name": "NrPartiiTowaru",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 1000,
            "min_length": 1,
            "max_length": 256,
        },
    )
    warunki_dostawy: None | str = field(
        default=None,
        metadata={
            "name": "WarunkiDostawy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    kurs_umowny: None | str = field(
        default=None,
        metadata={
            "name": "KursUmowny",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )
    waluta_umowna: None | TkodWaluty = field(
        default=None,
        metadata={
            "name": "WalutaUmowna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    transport: list[FakturaFaWarunkiTransakcjiTransport] = field(
        default_factory=list,
        metadata={
            "name": "Transport",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 20,
        },
    )
    podmiot_posredniczacy: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "PodmiotPosredniczacy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznikBlokDanych:
    """
    Attributes:
        znaglowek: Nagłówek bloku danych
        meta_dane: Dane opisowe
        tekst: Część tekstowa bloku danych
        tabela: Tabele
    """

    class Meta:
        global_type = False

    znaglowek: None | str = field(
        default=None,
        metadata={
            "name": "ZNaglowek",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 512,
        },
    )
    meta_dane: list[FakturaZalacznikBlokDanychMetaDane] = field(
        default_factory=list,
        metadata={
            "name": "MetaDane",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )
    tekst: None | FakturaZalacznikBlokDanychTekst = field(
        default=None,
        metadata={
            "name": "Tekst",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    tabela: list[FakturaZalacznikBlokDanychTabela] = field(
        default_factory=list,
        metadata={
            "name": "Tabela",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 1000,
        },
    )


@dataclass(kw_only=True)
class FakturaFa:
    """
    Attributes:
        kod_waluty: Kod waluty (ISO 4217)
        p_1: Data wystawienia, z zastrzeżeniem art. 106na ust. 1 ustawy
        p_1_m: Miejsce wystawienia faktury
        p_2: Kolejny numer faktury, nadany w ramach jednej lub więcej
            serii, który w sposób jednoznaczny identyfikuje fakturę
        wz: Numery dokumentów magazynowych WZ (wydanie na zewnątrz)
            związane z fakturą
        p_6: Data dokonania lub zakończenia dostawy towarów lub
            wykonania usługi lub data otrzymania zapłaty, o której mowa
            w art. 106b ust. 1 pkt 4 ustawy, o ile taka data jest
            określona i różni się od daty wystawienia faktury. Pole
            wypełnia się w przypadku, gdy dla wszystkich pozycji faktury
            data jest wspólna
        okres_fa: Okres, którego dotyczy faktura - w przypadkach, o
            których mowa w art. 19a ust. 3 zdanie pierwsze i ust. 4 oraz
            ust. 5 pkt 4 ustawy
        p_13_1: Suma wartości sprzedaży netto objętej stawką podstawową
            - aktualnie 23% albo 22%. W przypadku faktur zaliczkowych -
            wartość zaliczki netto. W przypadku faktur korygujących -
            kwota różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_14_1: Kwota podatku od sumy wartości sprzedaży netto objętej
            stawką podstawową - aktualnie 23% albo 22%. W przypadku
            faktur zaliczkowych - kwota podatku wyliczona według wzoru,
            o którym mowa w art. 106f ust. 1 pkt 3 ustawy. W przypadku
            faktur korygujących - kwota różnicy, o której mowa w art.
            106j ust. 2 pkt 5 ustawy
        p_14_1_w: W przypadku gdy faktura jest wystawiona w walucie
            obcej - kwota podatku od sumy wartości sprzedaży netto
            objętej stawką podstawową, przeliczona zgodnie z przepisami
            działu VI w związku z art. 106e ust. 11 ustawy - aktualnie
            23% albo 22%. W przypadku faktur zaliczkowych - kwota
            podatku wyliczona według wzoru, o którym mowa w art. 106f
            ust. 1 pkt 3 ustawy. W przypadku faktur korygujących - kwota
            różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_13_2: Suma wartości sprzedaży netto objętej stawką obniżoną
            pierwszą - aktualnie 8 % albo 7%. W przypadku faktur
            zaliczkowych - wartość zaliczki netto. W przypadku faktur
            korygujących - kwota różnicy, o której mowa w art. 106j ust.
            2 pkt 5 ustawy
        p_14_2: Kwota podatku od sumy wartości sprzedaży netto objętej
            stawką obniżoną pierwszą - aktualnie 8% albo 7%. W przypadku
            faktur zaliczkowych - kwota podatku wyliczona według wzoru,
            o którym mowa w art. 106f ust. 1 pkt 3 ustawy. W przypadku
            faktur korygujących - kwota różnicy, o której mowa w art.
            106j ust. 2 pkt 5 ustawy
        p_14_2_w: W przypadku gdy faktura jest wystawiona w walucie
            obcej - kwota podatku od sumy wartości sprzedaży netto
            objętej stawką obniżoną pierwszą, przeliczona zgodnie z
            przepisami działu VI w związku z art. 106e ust. 11 ustawy -
            aktualnie 8% albo 7%. W przypadku faktur zaliczkowych -
            kwota podatku wyliczona według wzoru, o którym mowa w art.
            106f ust. 1 pkt 3 ustawy. W przypadku faktur korygujących -
            kwota różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_13_3: Suma wartości sprzedaży netto objętej stawką obniżoną
            drugą - aktualnie 5%. W przypadku faktur zaliczkowych -
            wartość zaliczki netto. W przypadku faktur korygujących -
            kwota różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_14_3: Kwota podatku od sumy wartości sprzedaży netto objętej
            stawką obniżoną drugą - aktualnie 5%. W przypadku faktur
            zaliczkowych - kwota podatku wyliczona według wzoru, o
            którym mowa w art. 106f ust. 1 pkt 3 ustawy. W przypadku
            faktur korygujących - kwota różnicy, o której mowa w art.
            106j ust. 2 pkt 5 ustawy
        p_14_3_w: W przypadku gdy faktura jest wystawiona w walucie
            obcej - kwota podatku od sumy wartości sprzedaży netto
            objętej stawką obniżoną drugą, przeliczona zgodnie z
            przepisami działu VI w związku z art. 106e ust. 11 ustawy -
            aktualnie 5%. W przypadku faktur zaliczkowych - kwota
            podatku wyliczona według wzoru, o którym mowa w art. 106f
            ust. 1 pkt 3 ustawy. W przypadku faktur korygujących - kwota
            różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_13_4: Suma wartości sprzedaży netto objętej ryczałtem dla
            taksówek osobowych. W przypadku faktur zaliczkowych -
            wartość zaliczki netto. W przypadku faktur korygujących -
            kwota różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_14_4: Kwota podatku od sumy wartości sprzedaży netto w
            przypadku ryczałtu dla taksówek osobowych. W przypadku
            faktur zaliczkowych - kwota podatku wyliczona według wzoru,
            o którym mowa w art. 106f ust. 1 pkt 3 ustawy. W przypadku
            faktur korygujących - kwota różnicy, o której mowa w art.
            106j ust. 2 pkt 5 ustawy
        p_14_4_w: W przypadku gdy faktura jest wystawiona w walucie
            obcej - wysokość ryczałtu dla taksówek osobowych,
            przeliczona zgodnie z przepisami działu VI w związku z art.
            106e ust. 11 ustawy. W przypadku faktur zaliczkowych - kwota
            podatku wyliczona według wzoru, o którym mowa w art. 106f
            ust. 1 pkt 3 ustawy. W przypadku faktur korygujących - kwota
            różnicy, o której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_13_5: Suma wartości sprzedaży netto w przypadku procedury
            szczególnej, o której mowa w dziale XII w rozdziale 6a
            ustawy. W przypadku faktur zaliczkowych - wartość zaliczki
            netto. W przypadku faktur korygujących - kwota różnicy, o
            której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_14_5: Kwota podatku od wartości dodanej w przypadku procedury
            szczególnej, o której mowa w dziale XII w rozdziale 6a
            ustawy. W przypadku faktur zaliczkowych - kwota podatku
            wyliczona według wzoru, o którym mowa w art. 106f ust. 1 pkt
            3 ustawy. W przypadku faktur korygujących - kwota różnicy, o
            której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_13_6_1: Suma wartości sprzedaży objętej stawką 0% z
            wyłączeniem wewnątrzwspólnotowej dostawy towarów i eksportu.
            W przypadku faktur zaliczkowych - wartość zaliczki. W
            przypadku faktur korygujących - kwota różnicy, o której mowa
            w art. 106j ust. 2 pkt 5 ustawy
        p_13_6_2: Suma wartości sprzedaży objętej stawką 0% w przypadku
            wewnątrzwspólnotowej dostawy towarów. W przypadku faktur
            korygujących - kwota różnicy, o której mowa w art. 106j ust.
            2 pkt 5 ustawy
        p_13_6_3: Suma wartości sprzedaży objętej stawką 0% w przypadku
            eksportu. W przypadku faktur zaliczkowych - wartość
            zaliczki. W przypadku faktur korygujących - kwota różnicy, o
            której mowa w art. 106j ust. 2 pkt 5 ustawy
        p_13_7: Suma wartości sprzedaży zwolnionej od podatku. W
            przypadku faktur zaliczkowych - wartość zaliczki. W
            przypadku faktur korygujących - kwota różnicy wartości
            sprzedaży
        p_13_8: Suma wartości sprzedaży w przypadku dostawy towarów oraz
            świadczenia usług poza terytorium kraju, z wyłączeniem kwot
            wykazanych w polach P_13_5 i P_13_9. W przypadku faktur
            zaliczkowych - wartość zaliczki. W przypadku faktur
            korygujących - kwota różnicy wartości sprzedaży
        p_13_9: Suma wartości świadczenia usług, o których mowa w art.
            100 ust. 1 pkt 4 ustawy. W przypadku faktur zaliczkowych -
            wartość zaliczki. W przypadku faktur korygujących - kwota
            różnicy wartości sprzedaży
        p_13_10: Suma wartości sprzedaży w procedurze odwrotnego
            obciążenia, dla której podatnikiem jest nabywca zgodnie z
            art. 17 ust. 1 pkt 7 i 8 ustawy oraz innych przypadków
            odwrotnego obciążenia występujących w obrocie krajowym. W
            przypadku faktur zaliczkowych - wartość zaliczki. W
            przypadku faktur korygujących - kwota różnicy, o której mowa
            w art. 106j ust. 2 pkt 5 ustawy
        p_13_11: Suma wartości sprzedaży w procedurze marży, o której
            mowa w art. 119 i art. 120 ustawy. W przypadku faktur
            zaliczkowych - wartość zaliczki. W przypadku faktur
            korygujących - kwota różnicy wartości sprzedaży
        p_15: Kwota należności ogółem. W przypadku faktur zaliczkowych -
            kwota zapłaty dokumentowana fakturą. W przypadku faktur, o
            których mowa w art. 106f ust. 3 ustawy - kwota pozostała do
            zapłaty. W przypadku faktur korygujących - korekta kwoty
            wynikającej z faktury korygowanej. W przypadku, o którym
            mowa w art. 106j ust. 3 ustawy - korekta kwot wynikających z
            faktur korygowanych
        kurs_waluty_z: Kurs waluty stosowany do wyliczenia kwoty podatku
            w przypadkach, o których mowa w dziale VI ustawy na
            fakturach, o których mowa w art. 106b ust. 1 pkt 4 ustawy
        adnotacje: Inne adnotacje na fakturze
        rodzaj_faktury: Rodzaj faktury
        przyczyna_korekty: Przyczyna korekty dla faktur korygujących
        typ_korekty: Typ skutku korekty w ewidencji dla podatku od
            towarów i usług
        dane_fa_korygowanej: Dane faktury korygowanej
        okres_fa_korygowanej: Dla faktury korygującej, o której mowa w
            art. 106j ust. 3 ustawy - okres, do którego odnosi się
            udzielany opust lub udzielana obniżka, w przypadku gdy
            podatnik udziela opustu lub obniżki ceny w odniesieniu do
            dostaw towarów lub usług dokonanych lub świadczonych na
            rzecz jednego odbiorcy w danym okresie
        nr_fa_korygowany: Poprawny numer faktury korygowanej w
            przypadku, gdy przyczyną korekty jest błędny numer faktury
            korygowanej. W takim przypadku błędny numer faktury należy
            wskazać w polu NrFaKorygowanej
        podmiot1_k: W przypadku korekty danych sprzedawcy należy podać
            pełne dane sprzedawcy występujące na fakturze korygowanej.
            Pole nie dotyczy przypadku korekty błędnego NIP
            występującego na fakturze pierwotnej - wówczas wymagana jest
            korekta faktury do wartości zerowych
        podmiot2_k: W przypadku korekty danych nabywcy występującego
            jako Podmiot2 lub dodatkowego nabywcy występującego jako
            Podmiot3 należy podać pełne dane tego podmiotu występujące
            na fakturze korygowanej. Korekcie nie podlegają błędne
            numery NIP identyfikujące nabywcę oraz dodatkowego nabywcę -
            wówczas wymagana jest korekta faktury do wartości zerowych.
            W przypadku korygowania pozostałych danych nabywcy lub
            dodatkowego nabywcy wskazany numer identyfikacyjny ma być
            tożsamy z numerem w części Podmiot2 względnie Podmiot3
            faktury korygującej
        p_15_zk: W przypadku korekt faktur zaliczkowych - kwota zapłaty
            przed korektą. W przypadku korekt faktur, o których mowa w
            art. 106f ust. 3 ustawy - kwota pozostała do zapłaty przed
            korektą
        kurs_waluty_zk: Kurs waluty stosowany do wyliczenia kwoty
            podatku w przypadkach, o których mowa w dziale VI ustawy
            przed korektą
        zaliczka_czesciowa: Dane dla przypadków faktur dokumentujących
            otrzymanie więcej niż jednej płatności, o której mowa w art.
            106b ust. 1 pkt 4 ustawy. W przypadku, gdy faktura, o której
            mowa w art. 106f ust. 3 ustawy dokumentuje jednocześnie
            otrzymanie części zapłaty przed dokonaniem czynności,
            różnica kwoty w polu P_15 i sumy poszczególnych pól P_15Z
            stanowi kwotę pozostałą ponad płatności otrzymane przed
            wykonaniem czynności udokumentowanej fakturą
        fp: Faktura, o której mowa w art. 109 ust. 3d ustawy
        tp: Istniejące powiązania między nabywcą a dokonującym dostawy
            towarów lub usługodawcą, zgodnie z § 10 ust. 4 pkt 3, z
            zastrzeżeniem ust. 4b rozporządzenia w sprawie szczegółowego
            zakresu danych zawartych w deklaracjach podatkowych i w
            ewidencji w zakresie podatku od towarów i usług
        dodatkowy_opis: Pola przeznaczone dla wykazywania dodatkowych
            danych na fakturze, w tym wymaganych przepisami prawa, dla
            których nie przewidziano innych pól/elementów
        faktura_zaliczkowa: Numery faktur zaliczkowych lub ich numery
            KSeF, jeśli zostały wystawione z użyciem KSeF
        zwrot_akcyzy: Informacja dodatkowa niezbędna dla rolników
            ubiegających się o zwrot podatku akcyzowego zawartego w
            cenie oleju napędowego
        fa_wiersz: Szczegółowe pozycje faktury w walucie, w której
            wystawiono fakturę - węzeł opcjonalny dla faktury
            zaliczkowej, faktury korygującej fakturę zaliczkową oraz
            faktur korygujących dotyczących wszystkich dostaw towarów
            lub usług dokonanych lub świadczonych w danym okresie, o
            których mowa w art. 106j ust. 3 ustawy, dla których należy
            podać dane dotyczące opustu lub obniżki w podziale na stawki
            podatku i procedury w części Fa. W przypadku faktur
            korygujących, o których mowa w art. 106j ust. 3 ustawy, gdy
            opust lub obniżka ceny odnosi się do części dostaw towarów
            lub usług dokonanych lub świadczonych w danym okresie w
            części FaWiersz należy podać nazwy (rodzaje) towarów lub
            usług objętych korektą. W przypadku faktur, o których mowa w
            art. 106f ust. 3 ustawy, należy wykazać pełne wartości
            zamówienia lub umowy. W przypadku faktur korygujących
            pozycje faktury (w tym faktur korygujących faktury, o
            których mowa w art. 106f ust. 3 ustawy, jeśli korekta
            dotyczy wartości zamówienia) należy wykazać różnice
            wynikające z korekty poszczególnych pozycji lub dane pozycji
            korygowanych wg stanu przed korektą i po korekcie jako
            osobne wiersze. W przypadku faktur korygujących faktury, o
            których mowa w art. 106f ust. 3 ustawy, jeśli korekta nie
            dotyczy wartości zamówienia i jednocześnie zmienia wysokość
            podstawy opodatkowania lub podatku, należy wprowadzić zapis
            wg stanu przed korektą i zapis wg stanu po korekcie w celu
            potwierdzenia braku zmiany wartości danej pozycji faktury
        rozliczenie: Dodatkowe rozliczenia na fakturze
        platnosc: Warunki płatności
        warunki_transakcji: Warunki transakcji, o ile występują
        zamowienie: Zamówienie lub umowa, o których mowa w art. 106f
            ust. 1 pkt 4 ustawy (dla faktur zaliczkowych), w walucie, w
            której wystawiono fakturę zaliczkową. W przypadku faktury
            korygującej fakturę zaliczkową należy wykazać różnice
            wynikające z korekty poszczególnych pozycji zamówienia lub
            umowy lub dane pozycji korygowanych wg stanu przed korektą i
            po korekcie jako osobne wiersze, jeśli korekta dotyczy
            wartości zamówienia lub umowy. W przypadku faktur
            korygujących faktury zaliczkowe, jeśli korekta nie dotyczy
            wartości zamówienia lub umowy i jednocześnie zmienia
            wysokość podstawy opodatkowania lub podatku, należy
            wprowadzić zapis wg stanu przed korektą i zapis wg stanu po
            korekcie w celu potwierdzenia braku zmiany wartości danej
            pozycji
    """

    class Meta:
        global_type = False

    kod_waluty: TkodWaluty = field(
        metadata={
            "name": "KodWaluty",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    p_1: str = field(
        metadata={
            "name": "P_1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    p_1_m: None | str = field(
        default=None,
        metadata={
            "name": "P_1M",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_2: str = field(
        metadata={
            "name": "P_2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        }
    )
    wz: list[str] = field(
        default_factory=list,
        metadata={
            "name": "WZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 1000,
            "min_length": 1,
            "max_length": 256,
        },
    )
    p_6: None | str = field(
        default=None,
        metadata={
            "name": "P_6",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_inclusive": "2006-01-01",
            "max_inclusive": "2050-01-01",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        },
    )
    okres_fa: None | FakturaFaOkresFa = field(
        default=None,
        metadata={
            "name": "OkresFa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    p_13_1: None | str = field(
        default=None,
        metadata={
            "name": "P_13_1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_1: None | str = field(
        default=None,
        metadata={
            "name": "P_14_1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_1_w: None | str = field(
        default=None,
        metadata={
            "name": "P_14_1W",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_2: None | str = field(
        default=None,
        metadata={
            "name": "P_13_2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_2: None | str = field(
        default=None,
        metadata={
            "name": "P_14_2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_2_w: None | str = field(
        default=None,
        metadata={
            "name": "P_14_2W",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_3: None | str = field(
        default=None,
        metadata={
            "name": "P_13_3",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_3: None | str = field(
        default=None,
        metadata={
            "name": "P_14_3",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_3_w: None | str = field(
        default=None,
        metadata={
            "name": "P_14_3W",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_4: None | str = field(
        default=None,
        metadata={
            "name": "P_13_4",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_4: None | str = field(
        default=None,
        metadata={
            "name": "P_14_4",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_4_w: None | str = field(
        default=None,
        metadata={
            "name": "P_14_4W",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_5: None | str = field(
        default=None,
        metadata={
            "name": "P_13_5",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_14_5: None | str = field(
        default=None,
        metadata={
            "name": "P_14_5",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_6_1: None | str = field(
        default=None,
        metadata={
            "name": "P_13_6_1",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_6_2: None | str = field(
        default=None,
        metadata={
            "name": "P_13_6_2",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_6_3: None | str = field(
        default=None,
        metadata={
            "name": "P_13_6_3",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_7: None | str = field(
        default=None,
        metadata={
            "name": "P_13_7",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_8: None | str = field(
        default=None,
        metadata={
            "name": "P_13_8",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_9: None | str = field(
        default=None,
        metadata={
            "name": "P_13_9",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_10: None | str = field(
        default=None,
        metadata={
            "name": "P_13_10",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_13_11: None | str = field(
        default=None,
        metadata={
            "name": "P_13_11",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    p_15: str = field(
        metadata={
            "name": "P_15",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        }
    )
    kurs_waluty_z: None | str = field(
        default=None,
        metadata={
            "name": "KursWalutyZ",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )
    adnotacje: FakturaFaAdnotacje = field(
        metadata={
            "name": "Adnotacje",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    rodzaj_faktury: TrodzajFaktury = field(
        metadata={
            "name": "RodzajFaktury",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "required": True,
        }
    )
    przyczyna_korekty: None | str = field(
        default=None,
        metadata={
            "name": "PrzyczynaKorekty",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    typ_korekty: None | TtypKorekty = field(
        default=None,
        metadata={
            "name": "TypKorekty",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dane_fa_korygowanej: list[FakturaFaDaneFaKorygowanej] = field(
        default_factory=list,
        metadata={
            "name": "DaneFaKorygowanej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 50000,
        },
    )
    okres_fa_korygowanej: None | str = field(
        default=None,
        metadata={
            "name": "OkresFaKorygowanej",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    nr_fa_korygowany: None | str = field(
        default=None,
        metadata={
            "name": "NrFaKorygowany",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_length": 1,
            "max_length": 256,
        },
    )
    podmiot1_k: None | FakturaFaPodmiot1K = field(
        default=None,
        metadata={
            "name": "Podmiot1K",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    podmiot2_k: list[FakturaFaPodmiot2K] = field(
        default_factory=list,
        metadata={
            "name": "Podmiot2K",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 101,
        },
    )
    p_15_zk: None | str = field(
        default=None,
        metadata={
            "name": "P_15ZK",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 18,
            "fraction_digits": 2,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,2})?",
        },
    )
    kurs_waluty_zk: None | str = field(
        default=None,
        metadata={
            "name": "KursWalutyZK",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "total_digits": 22,
            "fraction_digits": 6,
            "pattern": r"-?([1-9]\d{0,15}|0)(\.\d{1,6})?",
        },
    )
    zaliczka_czesciowa: list[FakturaFaZaliczkaCzesciowa] = field(
        default_factory=list,
        metadata={
            "name": "ZaliczkaCzesciowa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 31,
        },
    )
    fp: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "FP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    tp: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "TP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    dodatkowy_opis: list[TkluczWartosc] = field(
        default_factory=list,
        metadata={
            "name": "DodatkowyOpis",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 10000,
        },
    )
    faktura_zaliczkowa: list[FakturaFaFakturaZaliczkowa] = field(
        default_factory=list,
        metadata={
            "name": "FakturaZaliczkowa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 100,
        },
    )
    zwrot_akcyzy: None | Twybor1 = field(
        default=None,
        metadata={
            "name": "ZwrotAkcyzy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    fa_wiersz: list[FakturaFaFaWiersz] = field(
        default_factory=list,
        metadata={
            "name": "FaWiersz",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "max_occurs": 10000,
        },
    )
    rozliczenie: None | FakturaFaRozliczenie = field(
        default=None,
        metadata={
            "name": "Rozliczenie",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    platnosc: None | FakturaFaPlatnosc = field(
        default=None,
        metadata={
            "name": "Platnosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    warunki_transakcji: None | FakturaFaWarunkiTransakcji = field(
        default=None,
        metadata={
            "name": "WarunkiTransakcji",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )
    zamowienie: None | FakturaFaZamowienie = field(
        default=None,
        metadata={
            "name": "Zamowienie",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
        },
    )


@dataclass(kw_only=True)
class FakturaZalacznik:
    """
    Attributes:
        blok_danych: Szczegółowe dane załącznika
    """

    class Meta:
        global_type = False

    blok_danych: list[FakturaZalacznikBlokDanych] = field(
        default_factory=list,
        metadata={
            "name": "BlokDanych",
            "type": "Element",
            "namespace": "http://crd.gov.pl/wzor/2025/06/25/13775/",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )


@dataclass(kw_only=True)
class Faktura:
    """
    Faktura VAT.

    Attributes:
        naglowek: Nagłówek
        podmiot1: Dane podatnika. Imię i nazwisko lub nazwa sprzedawcy
            towarów lub usług
        podmiot2: Dane nabywcy
        podmiot3: Dane podmiotu/-ów trzeciego/-ich (innego/-ych niż
            sprzedawca i nabywca wymieniony w części Podmiot2),
            związanego/-ych z fakturą
        podmiot_upowazniony: Dane podmiotu upoważnionego, związanego z
            fakturą
        fa: Na podstawie art. 106a - 106q ustawy. Pola dotyczące
            wartości sprzedaży i podatku wypełnia się w walucie, w
            której wystawiono fakturę, z wyjątkiem pól dotyczących
            podatku przeliczonego zgodnie z przepisami działu VI w
            związku z art. 106e ust. 11 ustawy. W przypadku wystawienia
            faktury korygującej wypełnia się wszystkie pola wg stanu po
            korekcie, a pola dotyczące podstaw opodatkowania, podatku
            oraz należności ogółem wypełnia się poprzez różnicę
        stopka: Pozostałe dane na fakturze
        zalacznik: Załącznik do faktury VAT
    """

    class Meta:
        namespace = "http://crd.gov.pl/wzor/2025/06/25/13775/"

    naglowek: Tnaglowek = field(
        metadata={
            "name": "Naglowek",
            "type": "Element",
            "required": True,
        }
    )
    podmiot1: FakturaPodmiot1 = field(
        metadata={
            "name": "Podmiot1",
            "type": "Element",
            "required": True,
        }
    )
    podmiot2: FakturaPodmiot2 = field(
        metadata={
            "name": "Podmiot2",
            "type": "Element",
            "required": True,
        }
    )
    podmiot3: list[FakturaPodmiot3] = field(
        default_factory=list,
        metadata={
            "name": "Podmiot3",
            "type": "Element",
            "max_occurs": 100,
        },
    )
    podmiot_upowazniony: None | FakturaPodmiotUpowazniony = field(
        default=None,
        metadata={
            "name": "PodmiotUpowazniony",
            "type": "Element",
        },
    )
    fa: FakturaFa = field(
        metadata={
            "name": "Fa",
            "type": "Element",
            "required": True,
        }
    )
    stopka: None | FakturaStopka = field(
        default=None,
        metadata={
            "name": "Stopka",
            "type": "Element",
        },
    )
    zalacznik: None | FakturaZalacznik = field(
        default=None,
        metadata={
            "name": "Zalacznik",
            "type": "Element",
        },
    )
