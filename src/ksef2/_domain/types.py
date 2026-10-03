from typing import Literal, NotRequired, TypedDict


class OffsetPaginationQueryParams(TypedDict):
    """Wire-format query parameters for offset-paginated endpoints."""

    pageOffset: NotRequired[int | None]
    """Zero-based index of the page to return."""
    pageSize: NotRequired[int | None]
    """Number of results per page."""


class InvoiceMetadataQueryParams(TypedDict):
    """Wire-format query parameters for invoice metadata queries."""

    sortOrder: NotRequired[str | None]
    """Sort direction, ``Asc`` or ``Desc``."""
    pageOffset: NotRequired[int | None]
    """Zero-based index of the page to return."""
    pageSize: NotRequired[int | None]
    """Number of results per page."""


class ListSessionsQueryParams(TypedDict):
    """Wire-format query parameters for listing sessions."""

    pageSize: NotRequired[int | None]
    """Number of results per page."""
    sessionType: Literal["Online", "Batch"]
    """Kind of sessions to list."""
    referenceNumber: NotRequired[str | None]
    """Match this session reference number."""
    dateCreatedFrom: NotRequired[str | None]
    """Match sessions created at or after this ISO 8601 time."""
    dateCreatedTo: NotRequired[str | None]
    """Match sessions created at or before this ISO 8601 time."""
    dateClosedFrom: NotRequired[str | None]
    """Match sessions closed at or after this ISO 8601 time."""
    dateClosedTo: NotRequired[str | None]
    """Match sessions closed at or before this ISO 8601 time."""
    dateModifiedFrom: NotRequired[str | None]
    """Match sessions modified at or after this ISO 8601 time."""
    dateModifiedTo: NotRequired[str | None]
    """Match sessions modified at or before this ISO 8601 time."""
    statuses: NotRequired[
        list[Literal["InProgress", "Succeeded", "Failed", "Cancelled"]] | None
    ]
    """Match sessions in any of these statuses."""


class ListTokensQueryParams(TypedDict):
    """Wire-format query parameters for listing tokens."""

    status: NotRequired[list[str] | None]
    """Match tokens in any of these statuses."""
    description: NotRequired[str | None]
    """Match tokens whose description contains this text."""
    authorIdentifier: NotRequired[str | None]
    """Match tokens created by this identifier."""
    authorIdentifierType: NotRequired[str | None]
    """Kind of identifier in ``authorIdentifier``."""
    pageSize: NotRequired[int | None]
    """Number of results per page."""


class CollectiveIdentifierQueryParams(TypedDict):
    """Wire-format query parameters for collective identifier queries."""

    pageSize: NotRequired[int | None]
    """Number of results per page."""


type CurrencyCodes = Literal[
    "AED",
    "AFN",
    "ALL",
    "AMD",
    "ANG",
    "AOA",
    "ARS",
    "AUD",
    "AWG",
    "AZN",
    "BAM",
    "BBD",
    "BDT",
    "BGN",
    "BHD",
    "BIF",
    "BMD",
    "BND",
    "BOB",
    "BOV",
    "BRL",
    "BSD",
    "BTN",
    "BWP",
    "BYN",
    "BZD",
    "CAD",
    "CDF",
    "CHE",
    "CHF",
    "CHW",
    "CLF",
    "CLP",
    "CNY",
    "COP",
    "COU",
    "CRC",
    "CUC",
    "CUP",
    "CVE",
    "CZK",
    "DJF",
    "DKK",
    "DOP",
    "DZD",
    "EGP",
    "ERN",
    "ETB",
    "EUR",
    "FJD",
    "FKP",
    "GBP",
    "GEL",
    "GGP",
    "GHS",
    "GIP",
    "GMD",
    "GNF",
    "GTQ",
    "GYD",
    "HKD",
    "HNL",
    "HRK",
    "HTG",
    "HUF",
    "IDR",
    "ILS",
    "IMP",
    "INR",
    "IQD",
    "IRR",
    "ISK",
    "JEP",
    "JMD",
    "JOD",
    "JPY",
    "KES",
    "KGS",
    "KHR",
    "KMF",
    "KPW",
    "KRW",
    "KWD",
    "KYD",
    "KZT",
    "LAK",
    "LBP",
    "LKR",
    "LRD",
    "LSL",
    "LYD",
    "MAD",
    "MDL",
    "MGA",
    "MKD",
    "MMK",
    "MNT",
    "MOP",
    "MRU",
    "MUR",
    "MVR",
    "MWK",
    "MXN",
    "MXV",
    "MYR",
    "MZN",
    "NAD",
    "NGN",
    "NIO",
    "NOK",
    "NPR",
    "NZD",
    "OMR",
    "PAB",
    "PEN",
    "PGK",
    "PHP",
    "PKR",
    "PLN",
    "PYG",
    "QAR",
    "RON",
    "RSD",
    "RUB",
    "RWF",
    "SAR",
    "SBD",
    "SCR",
    "SDG",
    "SEK",
    "SGD",
    "SHP",
    "SLL",
    "SOS",
    "SRD",
    "SSP",
    "STN",
    "SVC",
    "SYP",
    "SZL",
    "THB",
    "TJS",
    "TMT",
    "TND",
    "TOP",
    "TRY",
    "TTD",
    "TWD",
    "TZS",
    "UAH",
    "UGX",
    "USD",
    "USN",
    "UYI",
    "UYU",
    "UYW",
    "UZS",
    "VES",
    "VND",
    "VUV",
    "WST",
    "XAF",
    "XAG",
    "XAU",
    "XBA",
    "XBB",
    "XBC",
    "XBD",
    "XCD",
    "XCG",
    "XDR",
    "XOF",
    "XPD",
    "XPF",
    "XPT",
    "XSU",
    "XUA",
    "XXX",
    "YER",
    "ZAR",
    "ZMW",
    "ZWL",
]

KsefInvoiceTypes = Literal[
    "vat",  # Podstawowa (FA)
    "zal",  # Zaliczkowa (FA)
    "kor",  # Korygująca (FA)
    "roz",  # Rozliczeniowa (FA)
    "upr",  # Uproszczona (FA)
    "kor_zal",  # Korygująca fakturę zaliczkową (FA)
    "kor_roz",  # Korygująca fakturę rozliczeniową (FA)
    "vat_pef",  # Podstawowa (PEF)
    "vat_pef_sp",  # Specjalizowana (PEF)
    "kor_pef",  # Korygująca (PEF)
    "vat_rr",  # Podstawowa (RR)
    "kor_vat_rr",  # Korygująca (RR)
]
