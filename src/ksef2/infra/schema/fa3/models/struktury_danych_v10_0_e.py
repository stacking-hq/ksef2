from __future__ import annotations

from dataclasses import dataclass, field

from .kody_krajow_v10_0_e import TkodKraju

__NAMESPACE__ = (
    "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/"
)


@dataclass(kw_only=True)
class TidentyfikatorOsobyFizycznej:
    """
    Podstawowy zestaw danych identyfikacyjnych o osobie fizycznej.

    Attributes:
        nip: Identyfikator podatkowy NIP
        imie_pierwsze: Pierwsze imię
        nazwisko: Nazwisko
        data_urodzenia: Data urodzenia
        pesel: Identyfikator podatkowy numer PESEL
    """

    class Meta:
        name = "TIdentyfikatorOsobyFizycznej"

    nip: str = field(
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        }
    )
    imie_pierwsze: str = field(
        metadata={
            "name": "ImiePierwsze",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    nazwisko: str = field(
        metadata={
            "name": "Nazwisko",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 81,
        }
    )
    data_urodzenia: str = field(
        metadata={
            "name": "DataUrodzenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_inclusive": "1900-01-01",
            "max_inclusive": "2050-12-31",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    pesel: None | str = field(
        default=None,
        metadata={
            "name": "PESEL",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"\d{11}",
        },
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyFizycznej1:
    """
    Podstawowy zestaw danych identyfikacyjnych o osobie fizycznej z
    identyfikatorem NIP albo PESEL.

    Attributes:
        nip: Identyfikator podatkowy NIP
        pesel: Identyfikator podatkowy numer PESEL
        imie_pierwsze: Pierwsze imię
        nazwisko: Nazwisko
        data_urodzenia: Data urodzenia
    """

    class Meta:
        name = "TIdentyfikatorOsobyFizycznej1"

    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )
    pesel: None | str = field(
        default=None,
        metadata={
            "name": "PESEL",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"\d{11}",
        },
    )
    imie_pierwsze: str = field(
        metadata={
            "name": "ImiePierwsze",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    nazwisko: str = field(
        metadata={
            "name": "Nazwisko",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 81,
        }
    )
    data_urodzenia: str = field(
        metadata={
            "name": "DataUrodzenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_inclusive": "1900-01-01",
            "max_inclusive": "2050-12-31",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyFizycznej2:
    """
    Podstawowy zestaw danych identyfikacyjnych o osobie fizycznej z
    identyfikatorem NIP.

    Attributes:
        nip: Identyfikator podatkowy NIP
        imie_pierwsze: Pierwsze imię
        nazwisko: Nazwisko
        data_urodzenia: Data urodzenia
    """

    class Meta:
        name = "TIdentyfikatorOsobyFizycznej2"

    nip: str = field(
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        }
    )
    imie_pierwsze: str = field(
        metadata={
            "name": "ImiePierwsze",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    nazwisko: str = field(
        metadata={
            "name": "Nazwisko",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 81,
        }
    )
    data_urodzenia: str = field(
        metadata={
            "name": "DataUrodzenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_inclusive": "1900-01-01",
            "max_inclusive": "2050-12-31",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyFizycznejPelny:
    """
    Pełny zestaw danych identyfikacyjnych o osobie fizycznej.

    Attributes:
        nip: Identyfikator podatkowy NIP
        imie_pierwsze: Pierwsze imię
        nazwisko: Nazwisko
        data_urodzenia: Data urodzenia
        imie_ojca: Imię ojca
        imie_matki: Imię matki
        pesel: Identyfikator podatkowy numer PESEL
    """

    class Meta:
        name = "TIdentyfikatorOsobyFizycznejPelny"

    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )
    imie_pierwsze: str = field(
        metadata={
            "name": "ImiePierwsze",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    nazwisko: str = field(
        metadata={
            "name": "Nazwisko",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 81,
        }
    )
    data_urodzenia: str = field(
        metadata={
            "name": "DataUrodzenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_inclusive": "1900-01-01",
            "max_inclusive": "2050-12-31",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    imie_ojca: str = field(
        metadata={
            "name": "ImieOjca",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    imie_matki: str = field(
        metadata={
            "name": "ImieMatki",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    pesel: str = field(
        metadata={
            "name": "PESEL",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"\d{11}",
        }
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyFizycznejZagranicznej:
    """
    Zestaw danych identyfikacyjnych dla osoby fizycznej zagranicznej.

    Attributes:
        imie_pierwsze: Imię pierwsze [First name]
        nazwisko: Nazwisko [Family name]
        data_urodzenia: Data urodzenia [Date of Birth]
        miejsce_urodzenia: Miejsce urodzenia [Place of Birth]
        imie_ojca: Imię ojca [Father’s name]
        imie_matki: Imię matki [Mother’s name]
        nip: Identyfikator podatkowy NIP [Tax Identification Number
            (NIP)]
    """

    class Meta:
        name = "TIdentyfikatorOsobyFizycznejZagranicznej"

    imie_pierwsze: str = field(
        metadata={
            "name": "ImiePierwsze",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
    nazwisko: str = field(
        metadata={
            "name": "Nazwisko",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 81,
        }
    )
    data_urodzenia: str = field(
        metadata={
            "name": "DataUrodzenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_inclusive": "1900-01-01",
            "max_inclusive": "2050-12-31",
            "pattern": r"((\d{4})-(\d{2})-(\d{2}))",
        }
    )
    miejsce_urodzenia: str = field(
        metadata={
            "name": "MiejsceUrodzenia",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 56,
        }
    )
    imie_ojca: None | str = field(
        default=None,
        metadata={
            "name": "ImieOjca",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 30,
        },
    )
    imie_matki: None | str = field(
        default=None,
        metadata={
            "name": "ImieMatki",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 30,
        },
    )
    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyNiefizycznej:
    """
    Podstawowy zestaw danych identyfikacyjnych o osobie niefizycznej.

    Attributes:
        nip: Identyfikator podatkowy NIP
        pelna_nazwa: Pełna nazwa
        regon: Numer REGON
    """

    class Meta:
        name = "TIdentyfikatorOsobyNiefizycznej"

    nip: str = field(
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        }
    )
    pelna_nazwa: str = field(
        metadata={
            "name": "PelnaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 240,
        }
    )
    regon: None | str = field(
        default=None,
        metadata={
            "name": "REGON",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"\d{14}",
        },
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyNiefizycznej1:
    """
    Podstawowy zestaw danych identyfikacyjnych o osobie niefizycznej - bez
    elementu Numer REGON.

    Attributes:
        nip: Identyfikator podatkowy NIP
        pelna_nazwa: Pełna nazwa
    """

    class Meta:
        name = "TIdentyfikatorOsobyNiefizycznej1"

    nip: str = field(
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        }
    )
    pelna_nazwa: str = field(
        metadata={
            "name": "PelnaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 240,
        }
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyNiefizycznejPelny:
    """
    Pełny zestaw danych identyfikacyjnych o osobie niefizycznej.

    Attributes:
        nip: Identyfikator podatkowy NIP
        pelna_nazwa: Pełna nazwa
        skrocona_nazwa: Skrócona nazwa
        regon: Numer REGON
    """

    class Meta:
        name = "TIdentyfikatorOsobyNiefizycznejPelny"

    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )
    pelna_nazwa: str = field(
        metadata={
            "name": "PelnaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 240,
        }
    )
    skrocona_nazwa: str = field(
        metadata={
            "name": "SkroconaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 70,
        }
    )
    regon: str = field(
        metadata={
            "name": "REGON",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"\d{14}",
        }
    )


@dataclass(kw_only=True)
class TidentyfikatorOsobyNiefizycznejZagranicznej:
    """
    Zestaw danych identyfikacyjnych dla osoby niefizycznej zagranicznej.

    Attributes:
        pelna_nazwa: Pełna nazwa [Name]
        skrocona_nazwa: Nazwa skrócona [Short Name]
        nip: Identyfikator podatkowy NIP [Tax Identification Number
            (NIP)]
    """

    class Meta:
        name = "TIdentyfikatorOsobyNiefizycznejZagranicznej"

    pelna_nazwa: str = field(
        metadata={
            "name": "PelnaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 240,
        }
    )
    skrocona_nazwa: None | str = field(
        default=None,
        metadata={
            "name": "SkroconaNazwa",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 70,
        },
    )
    nip: None | str = field(
        default=None,
        metadata={
            "name": "NIP",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "pattern": r"[1-9]((\d[1-9])|([1-9]\d))\d{7}",
        },
    )


@dataclass(kw_only=True)
class TadresPolski:
    """
    Informacje opisujące adres polski.

    Attributes:
        kod_kraju: Kraj
        wojewodztwo: Województwo
        powiat: Powiat
        gmina: Gmina
        ulica: Nazwa ulicy
        nr_domu: Numer budynku
        nr_lokalu: Numer lokalu
        miejscowosc: Nazwa miejscowości
        kod_pocztowy: Kod pocztowy
        poczta: Nazwa urzędu pocztowego
    """

    class Meta:
        name = "TAdresPolski"

    kod_kraju: TkodKraju = field(
        init=False,
        default=TkodKraju.PL,
        metadata={
            "name": "KodKraju",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        },
    )
    wojewodztwo: str = field(
        metadata={
            "name": "Wojewodztwo",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 36,
        }
    )
    powiat: str = field(
        metadata={
            "name": "Powiat",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 36,
        }
    )
    gmina: str = field(
        metadata={
            "name": "Gmina",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 36,
        }
    )
    ulica: None | str = field(
        default=None,
        metadata={
            "name": "Ulica",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 65,
        },
    )
    nr_domu: str = field(
        metadata={
            "name": "NrDomu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 9,
        }
    )
    nr_lokalu: None | str = field(
        default=None,
        metadata={
            "name": "NrLokalu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 10,
        },
    )
    miejscowosc: str = field(
        metadata={
            "name": "Miejscowosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 56,
        }
    )
    kod_pocztowy: str = field(
        metadata={
            "name": "KodPocztowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 8,
        }
    )
    poczta: str = field(
        metadata={
            "name": "Poczta",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 56,
        }
    )


@dataclass(kw_only=True)
class TadresPolski1:
    """
    Informacje opisujące adres polski - bez elementu Poczta.

    Attributes:
        kod_kraju: Kraj
        wojewodztwo: Województwo
        powiat: Powiat
        gmina: Gmina
        ulica: Nazwa ulicy
        nr_domu: Numer budynku
        nr_lokalu: Numer lokalu
        miejscowosc: Nazwa miejscowości
        kod_pocztowy: Kod pocztowy
    """

    class Meta:
        name = "TAdresPolski1"

    kod_kraju: TkodKraju = field(
        init=False,
        default=TkodKraju.PL,
        metadata={
            "name": "KodKraju",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        },
    )
    wojewodztwo: str = field(
        metadata={
            "name": "Wojewodztwo",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 36,
        }
    )
    powiat: str = field(
        metadata={
            "name": "Powiat",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 36,
        }
    )
    gmina: str = field(
        metadata={
            "name": "Gmina",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 36,
        }
    )
    ulica: None | str = field(
        default=None,
        metadata={
            "name": "Ulica",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 65,
        },
    )
    nr_domu: str = field(
        metadata={
            "name": "NrDomu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 9,
        }
    )
    nr_lokalu: None | str = field(
        default=None,
        metadata={
            "name": "NrLokalu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 10,
        },
    )
    miejscowosc: str = field(
        metadata={
            "name": "Miejscowosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 56,
        }
    )
    kod_pocztowy: str = field(
        metadata={
            "name": "KodPocztowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 8,
        }
    )


@dataclass(kw_only=True)
class TadresZagraniczny:
    """
    Informacje opisujące adres zagraniczny.

    Attributes:
        kod_kraju: Kod Kraju [Country Code]
        kod_pocztowy: Kod pocztowy [Postal code]
        miejscowosc: Nazwa miejscowości [City]
        ulica: Nazwa ulicy [Street]
        nr_domu: Numer budynku [Building number]
        nr_lokalu: Numer lokalu [Flat number]
    """

    class Meta:
        name = "TAdresZagraniczny"

    kod_kraju: TkodKraju = field(
        metadata={
            "name": "KodKraju",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "pattern": r"P[A-KM-Z]|[A-OQ-Z][A-Z]",
        }
    )
    kod_pocztowy: None | str = field(
        default=None,
        metadata={
            "name": "KodPocztowy",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 8,
        },
    )
    miejscowosc: str = field(
        metadata={
            "name": "Miejscowosc",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
            "min_length": 1,
            "max_length": 56,
        }
    )
    ulica: None | str = field(
        default=None,
        metadata={
            "name": "Ulica",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 65,
        },
    )
    nr_domu: None | str = field(
        default=None,
        metadata={
            "name": "NrDomu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 9,
        },
    )
    nr_lokalu: None | str = field(
        default=None,
        metadata={
            "name": "NrLokalu",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "min_length": 1,
            "max_length": 10,
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyBezAdresu:
    """
    Skrócony zestaw danych o osobie fizycznej lub niefizycznej.
    """

    class Meta:
        name = "TPodmiotDowolnyBezAdresu"

    osoba_fizyczna: None | TidentyfikatorOsobyFizycznej = field(
        default=None,
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    osoba_niefizyczna: None | TidentyfikatorOsobyNiefizycznej = field(
        default=None,
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyBezAdresu1:
    """
    Skrócony zestaw danych o osobie fizycznej lub niefizycznej z
    identyfikatorem NIP albo PESEL.
    """

    class Meta:
        name = "TPodmiotDowolnyBezAdresu1"

    osoba_fizyczna: None | TidentyfikatorOsobyFizycznej1 = field(
        default=None,
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    osoba_niefizyczna: None | TidentyfikatorOsobyNiefizycznej = field(
        default=None,
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyBezAdresu2:
    """
    Skrócony zestaw danych o osobie fizycznej lub niefizycznej z
    identyfikatorem NIP.
    """

    class Meta:
        name = "TPodmiotDowolnyBezAdresu2"

    osoba_fizyczna: None | TidentyfikatorOsobyFizycznej2 = field(
        default=None,
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    osoba_niefizyczna: None | TidentyfikatorOsobyNiefizycznej = field(
        default=None,
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyBezAdresu3:
    """
    Skrócony zestaw danych o osobie fizycznej lub niefizycznej z
    identyfikatorem NIP - bez elementu numer REGON dla osoby niefizycznej.
    """

    class Meta:
        name = "TPodmiotDowolnyBezAdresu3"

    osoba_fizyczna: None | TidentyfikatorOsobyFizycznej2 = field(
        default=None,
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    osoba_niefizyczna: None | TidentyfikatorOsobyNiefizycznej1 = field(
        default=None,
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )


@dataclass(kw_only=True)
class Tadres:
    """
    Dane określające adres.
    """

    class Meta:
        name = "TAdres"

    adres_pol: None | TadresPolski = field(
        default=None,
        metadata={
            "name": "AdresPol",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    adres_zagr: None | TadresZagraniczny = field(
        default=None,
        metadata={
            "name": "AdresZagr",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )


@dataclass(kw_only=True)
class Tadres1:
    """
    Dane określające adres - bez elementu Poczta w adresie polskim.
    """

    class Meta:
        name = "TAdres1"

    adres_pol: None | TadresPolski1 = field(
        default=None,
        metadata={
            "name": "AdresPol",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    adres_zagr: None | TadresZagraniczny = field(
        default=None,
        metadata={
            "name": "AdresZagr",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )


@dataclass(kw_only=True)
class TosobaFizyczna1AdresZamieszkania(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizyczna2AdresZamieszkania(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizyczna3AdresZamieszkania(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizyczna4AdresZamieszkania(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizyczna5AdresZamieszkania(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizycznaPelna1AdresZamieszkania(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizycznaPelnaAdresZamieszkania(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizycznaAdresZamieszkania(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]Meta:
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaNiefizyczna1AdresSiedziby(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaNiefizyczna2AdresSiedziby(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaNiefizycznaPelna1AdresSiedziby(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaNiefizycznaPelnaAdresSiedziby(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaNiefizycznaAdresSiedziby(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolny1AdresZamieszkaniaSiedziby(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolny2AdresZamieszkaniaSiedziby(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyPelny1AdresZamieszkaniaSiedziby(Tadres1):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyPelnyAdresZamieszkaniaSiedziby(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyAdresZamieszkaniaSiedziby(Tadres):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        global_type = False

    rodzaj_adresu: str = field(
        init=False,
        default="RAD",
        metadata={
            "name": "rodzajAdresu",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass(kw_only=True)
class TosobaFizyczna:
    """
    Podstawowy zestaw danych o osobie fizycznej.
    """

    class Meta:
        name = "TOsobaFizyczna"

    osoba_fizyczna: TidentyfikatorOsobyFizycznej = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizycznaAdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizyczna1:
    """
    Podstawowy zestaw danych o osobie fizycznej z identyfikatorem NIP albo
    PESEL.
    """

    class Meta:
        name = "TOsobaFizyczna1"

    osoba_fizyczna: TidentyfikatorOsobyFizycznej1 = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizyczna1AdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizyczna2:
    """
    Podstawowy zestaw danych o osobie fizycznej z identyfikatorem NIP.
    """

    class Meta:
        name = "TOsobaFizyczna2"

    osoba_fizyczna: TidentyfikatorOsobyFizycznej2 = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizyczna2AdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizyczna3:
    """
    Podstawowy zestaw danych o osobie fizycznej z identyfikatorem NIP albo
    PESEL - bez elementu Poczta w adresie polskim.
    """

    class Meta:
        name = "TOsobaFizyczna3"

    osoba_fizyczna: TidentyfikatorOsobyFizycznej1 = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizyczna3AdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizyczna4:
    """
    Podstawowy zestaw danych o osobie fizycznej z identyfikatorem NIP - bez
    elementu Poczta w adresie polskim.
    """

    class Meta:
        name = "TOsobaFizyczna4"

    osoba_fizyczna: TidentyfikatorOsobyFizycznej2 = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizyczna4AdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizyczna5:
    """
    Podstawowy zestaw danych o osobie fizycznej - bez elementu Poczta w
    adresie polskim.
    """

    class Meta:
        name = "TOsobaFizyczna5"

    osoba_fizyczna: TidentyfikatorOsobyFizycznej = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizyczna5AdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizycznaPelna:
    """
    Pełny zestaw danych o osobie fizycznej.
    """

    class Meta:
        name = "TOsobaFizycznaPelna"

    osoba_fizyczna: TidentyfikatorOsobyFizycznejPelny = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizycznaPelnaAdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaFizycznaPelna1:
    """
    Pełny zestaw danych o osobie fizycznej - bez elementu Poczta w adresie
    polskim.
    """

    class Meta:
        name = "TOsobaFizycznaPelna1"

    osoba_fizyczna: TidentyfikatorOsobyFizycznejPelny = field(
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_zamieszkania: TosobaFizycznaPelna1AdresZamieszkania = field(
        metadata={
            "name": "AdresZamieszkania",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaNiefizyczna:
    """
    Podstawowy zestaw danych o osobie niefizycznej.
    """

    class Meta:
        name = "TOsobaNiefizyczna"

    osoba_niefizyczna: TidentyfikatorOsobyNiefizycznej = field(
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_siedziby: TosobaNiefizycznaAdresSiedziby = field(
        metadata={
            "name": "AdresSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaNiefizyczna1:
    """
    Podstawowy zestaw danych o osobie niefizycznej - bez elementu Poczta w
    adresie polskim.
    """

    class Meta:
        name = "TOsobaNiefizyczna1"

    osoba_niefizyczna: TidentyfikatorOsobyNiefizycznej = field(
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_siedziby: TosobaNiefizyczna1AdresSiedziby = field(
        metadata={
            "name": "AdresSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaNiefizyczna2:
    """
    Podstawowy zestaw danych o osobie niefizycznej - bez elementu Numer
    REGON oraz bez elementu Poczta w adresie polskim.
    """

    class Meta:
        name = "TOsobaNiefizyczna2"

    osoba_niefizyczna: TidentyfikatorOsobyNiefizycznej1 = field(
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_siedziby: TosobaNiefizyczna2AdresSiedziby = field(
        metadata={
            "name": "AdresSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaNiefizycznaPelna:
    """
    Pełny zestaw danych o niefizycznej.
    """

    class Meta:
        name = "TOsobaNiefizycznaPelna"

    osoba_niefizyczna: TidentyfikatorOsobyNiefizycznejPelny = field(
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_siedziby: TosobaNiefizycznaPelnaAdresSiedziby = field(
        metadata={
            "name": "AdresSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TosobaNiefizycznaPelna1:
    """
    Pełny zestaw danych o osobie niefizycznej - bez elementu Poczta w
    adresie polskim.
    """

    class Meta:
        name = "TOsobaNiefizycznaPelna1"

    osoba_niefizyczna: TidentyfikatorOsobyNiefizycznejPelny = field(
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
    adres_siedziby: TosobaNiefizycznaPelna1AdresSiedziby = field(
        metadata={
            "name": "AdresSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TpodmiotDowolny(TpodmiotDowolnyBezAdresu):
    """
    Podstawowy zestaw danych o osobie fizycznej lub niefizycznej.
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        name = "TPodmiotDowolny"

    adres_zamieszkania_siedziby: TpodmiotDowolnyAdresZamieszkaniaSiedziby = field(
        metadata={
            "name": "AdresZamieszkaniaSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TpodmiotDowolny1(TpodmiotDowolnyBezAdresu):
    """
    Podstawowy zestaw danych o osobie fizycznej lub niefizycznej - bez
    elementu Poczta w adresie polskim.
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        name = "TPodmiotDowolny1"

    adres_zamieszkania_siedziby: TpodmiotDowolny1AdresZamieszkaniaSiedziby = field(
        metadata={
            "name": "AdresZamieszkaniaSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TpodmiotDowolny2(TpodmiotDowolnyBezAdresu3):
    """
    Podstawowy zestaw danych o osobie fizycznej lub niefizycznej - bez
    elementu Numer REGON oraz bez elementu Poczta w adresie polskim.
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        name = "TPodmiotDowolny2"

    adres_zamieszkania_siedziby: TpodmiotDowolny2AdresZamieszkaniaSiedziby = field(
        metadata={
            "name": "AdresZamieszkaniaSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyPelny:
    """
    Pełny zestaw danych o osobie fizycznej lub niefizycznej.
    """

    class Meta:
        name = "TPodmiotDowolnyPelny"

    osoba_fizyczna: None | TidentyfikatorOsobyFizycznejPelny = field(
        default=None,
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    osoba_niefizyczna: None | TidentyfikatorOsobyNiefizycznejPelny = field(
        default=None,
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    adres_zamieszkania_siedziby: TpodmiotDowolnyPelnyAdresZamieszkaniaSiedziby = field(
        metadata={
            "name": "AdresZamieszkaniaSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TpodmiotDowolnyPelny1:
    """
    Pełny zestaw danych o osobie fizycznej lub niefizycznej - bez elementu
    Poczta w adresie polskim.
    """

    class Meta:
        name = "TPodmiotDowolnyPelny1"

    osoba_fizyczna: None | TidentyfikatorOsobyFizycznejPelny = field(
        default=None,
        metadata={
            "name": "OsobaFizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    osoba_niefizyczna: None | TidentyfikatorOsobyNiefizycznejPelny = field(
        default=None,
        metadata={
            "name": "OsobaNiefizyczna",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
        },
    )
    adres_zamieszkania_siedziby: TpodmiotDowolnyPelny1AdresZamieszkaniaSiedziby = field(
        metadata={
            "name": "AdresZamieszkaniaSiedziby",
            "type": "Element",
            "namespace": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/",
            "required": True,
        }
    )
