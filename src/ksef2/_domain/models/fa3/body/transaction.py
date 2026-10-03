"""FA(3) transaction condition and transport detail models."""

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from ksef2._domain.models import KSeFBaseModel


TransportType = Literal[
    "sea",
    "rail",
    "road",
    "air",
    "postal",
    "pipeline",
    "inland_waterway",
]

CargoType = Literal[
    "demijohn",
    "barrel",
    "cylinder",
    "carton",
    "canister",
    "crate",
    "container",
    "basket",
    "punnet",
    "bulk_package",
    "parcel",
    "bundle",
    "pallet",
    "bin",
    "dry_bulk_container",
    "liquid_bulk_container",
    "box",
    "can",
    "chest",
    "bag",
]


class TransactionAddress(KSeFBaseModel):
    """FA(3) transaction address structure.

    References:
        schemat.Tadres

    Maps:
        country_code - kod_kraju (str)
        address_line_1 - adres_l1 (str)
        address_line_2 - adres_l2 (str)
        gln - gln (str)
    """

    country_code: str
    """Two-letter ISO 3166 country code."""
    address_line_1: str
    """First address line, usually street and building number."""
    address_line_2: str | None = None
    """Second address line, usually postal code and city."""
    gln: str | None = None
    """Global Location Number of the address."""

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        """Normalize the country code to uppercase and check its format.

        Args:
            value: Country code to validate.

        Returns:
            The uppercase two-letter country code.

        Raises:
            ValueError: If the value is not two letters.
        """
        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{2}", normalized) is None:
            raise ValueError("country_code must be a 2-letter ISO code")
        return normalized


class TransactionIdentity(KSeFBaseModel):
    """FA(3) transaction party identification data.

    References:
        schemat.Tpodmiot2

    Maps:
        tax_id - nip (str)
        eu_vat_id - kod_ue + nr_vat_ue (str)
        country_code - kod_kraju (str)
        other_id - nr_id (str)
        no_id - brak_id (bool)
        name - nazwa (str)
    """

    tax_id: str | None = None
    """Polish NIP."""
    eu_vat_id: str | None = None
    """EU VAT identifier."""
    country_code: str | None = None
    """Two-letter country code accompanying ``other_id``."""
    other_id: str | None = None
    """Identifier of another kind."""
    name: str | None = None
    """Full name of the party."""
    no_id: bool = False
    """Marks a party that has no identifier."""

    @field_validator("eu_vat_id")
    @classmethod
    def normalize_eu_vat_id(cls, value: str | None) -> str | None:
        """Normalize the EU VAT identifier to uppercase.

        Args:
            value: EU VAT identifier, or ``None``.

        Returns:
            The uppercase identifier, or ``None``.
        """
        if value is None:
            return None
        return value.upper()

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str | None) -> str | None:
        """Normalize the country code to uppercase and check its format.

        Args:
            value: Country code, or ``None``.

        Returns:
            The uppercase two-letter country code, or ``None``.

        Raises:
            ValueError: If the value is not two letters.
        """
        if value is None:
            return None

        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{2}", normalized) is None:
            raise ValueError("country_code must be a 2-letter ISO code")
        return normalized

    @model_validator(mode="after")
    def validate_identifier_flags(self) -> Self:
        """Forbid combining ``no_id`` with other identifiers.

        Returns:
            The validated identity.

        Raises:
            ValueError: If ``no_id`` is set together with another identifier.
        """
        if self.no_id and any(
            value is not None
            for value in (self.tax_id, self.eu_vat_id, self.country_code, self.other_id)
        ):
            raise ValueError("no_id cannot be combined with other identifiers")
        return self


class TransactionContract(KSeFBaseModel):
    """FA(3) contract reference used in transaction conditions.

    References:
        schemat.FakturaFaWarunkiTransakcjiUmowy

    Maps:
        contract_date - data_umowy (date)
        contract_number - nr_umowy (str)
    """

    contract_date: date | None = None
    """Date of the contract."""
    contract_number: str | None = None
    """Number of the contract."""

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        """Require a contract date or number.

        Returns:
            The validated contract reference.

        Raises:
            ValueError: If neither ``contract_date`` nor ``contract_number`` is set.
        """
        if self.contract_date is None and self.contract_number is None:
            raise ValueError(
                "At least one of contract_date or contract_number must be provided"
            )
        return self


class TransactionOrder(KSeFBaseModel):
    """FA(3) order reference used in transaction conditions.

    References:
        schemat.FakturaFaWarunkiTransakcjiZamowienia

    Maps:
        order_date - data_zamowienia (date)
        order_number - nr_zamowienia (str)
    """

    order_date: date | None = None
    """Date of the order."""
    order_number: str | None = None
    """Number of the order."""

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        """Require an order date or number.

        Returns:
            The validated order reference.

        Raises:
            ValueError: If neither ``order_date`` nor ``order_number`` is set.
        """
        if self.order_date is None and self.order_number is None:
            raise ValueError(
                "At least one of order_date or order_number must be provided"
            )
        return self


class TransactionTransport(KSeFBaseModel):
    """FA(3) transport data nested under transaction conditions.

    References:
        schemat.FakturaFaWarunkiTransakcjiTransport

    Maps:
        transport_type - rodzaj_transportu (TransportType)
        other_transport - transport_inny (bool)
        other_transport_description - opis_innego_transportu (str)
        carrier_identity - przewoznik/dane_identyfikacyjne (Tpodmiot2)
        carrier_address - przewoznik/adres_przewoznika (Tadres)
        transport_order_number - nr_zlecenia_transportu (str)
        cargo_type - opis_ladunku (CargoType)
        other_cargo - ladunek_inny (bool)
        other_cargo_description - opis_innego_ladunku (str)
        packaging_unit - jednostka_opakowania (str)
        transport_start - data_godz_rozp_transportu (datetime)
        transport_end - data_godz_zak_transportu (datetime)
        shipping_from - wysylka_z (Tadres)
        shipping_via - wysylka_przez List(Tadres)
        shipping_to - wysylka_do (Tadres)
    """

    # --- transport ---
    transport_type: TransportType | None = None
    """Mode of transport."""
    other_transport: bool = False
    """Marks a mode of transport not in ``transport_type``; describe it in ``other_transport_description``."""
    other_transport_description: str | None = None
    """Description of the other mode of transport."""
    carrier_identity: TransactionIdentity | None = None
    """Identification of the carrier."""
    carrier_address: TransactionAddress | None = None
    """Address of the carrier."""
    transport_order_number: str | None = None
    """Number of the transport order."""
    # --- cargo ---
    cargo_type: CargoType | None = None
    """Type of cargo."""
    other_cargo: bool = False
    """Marks a cargo type not in ``cargo_type``; describe it in ``other_cargo_description``."""
    other_cargo_description: str | None = None
    """Description of the other cargo type."""
    packaging_unit: str | None = None
    """Packaging unit of the cargo."""
    # --- shipping ---
    transport_start: datetime | None = None
    """When the transport starts."""
    transport_end: datetime | None = None
    """When the transport ends."""
    shipping_from: TransactionAddress | None = None
    """Address the goods ship from."""
    shipping_via: list[TransactionAddress] = Field(default_factory=list, max_length=20)
    """Intermediate addresses the goods ship via (up to 20)."""
    shipping_to: TransactionAddress | None = None
    """Address the goods ship to."""

    def _validate_transport_details(self) -> None:
        if self.transport_type is not None and self.other_transport:
            raise ValueError(
                "transport_type cannot be combined with other_transport details"
            )
        if self.other_transport and self.other_transport_description is None:
            raise ValueError(
                "other_transport_description is required when other_transport is true"
            )
        if not self.other_transport and self.other_transport_description is not None:
            raise ValueError(
                "other_transport must be true when other_transport_description is provided"
            )

    def _validate_cargo_details(self) -> None:
        if self.cargo_type is not None and self.other_cargo:
            raise ValueError("cargo_type cannot be combined with other_cargo details")
        if self.other_cargo and self.other_cargo_description is None:
            raise ValueError(
                "other_cargo_description is required when other_cargo is true"
            )
        if not self.other_cargo and self.other_cargo_description is not None:
            raise ValueError(
                "other_cargo must be true when other_cargo_description is provided"
            )

    def _validate_carrier_details(self) -> None:
        if self.carrier_identity is not None and self.carrier_address is None:
            raise ValueError(
                "carrier_identity and carrier_address must be provided together"
            )
        if self.carrier_identity is None and self.carrier_address is not None:
            raise ValueError(
                "carrier_identity and carrier_address must be provided together"
            )

    @model_validator(mode="after")
    def validate_choices(self) -> Self:
        """Validate transport, cargo and carrier details and the transport period.

        Returns:
            The validated transport.

        Raises:
            ValueError: If the details are inconsistent or ``transport_start`` is later than ``transport_end``.
        """
        self._validate_transport_details()
        self._validate_cargo_details()
        self._validate_carrier_details()
        if (
            self.transport_start is not None
            and self.transport_end is not None
            and self.transport_start > self.transport_end
        ):
            raise ValueError("transport_start cannot be later than transport_end")

        return self


class TransactionConditions(KSeFBaseModel):
    """FA(3) transaction conditions attached to an invoice.

    References:
        schemat.FakturaFaWarunkiTransakcji

    Maps:
        contracts - umowy List(FakturaFaWarunkiTransakcjiUmowy)
        orders - zamowienia List(FakturaFaWarunkiTransakcjiZamowienia)
        lot_numbers - nr_partii_towaru List(str)
        delivery_terms - warunki_dostawy (str)
        contract_exchange_rate - kurs_umowny (Decimal)
        contract_currency - waluta_umowna (str)
        transports - transport List(FakturaFaWarunkiTransakcjiTransport)
        intermediary_entity - podmiot_posredniczacy (bool)
    """

    contracts: list[TransactionContract] = Field(default_factory=list)
    """Contracts the transaction refers to."""
    orders: list[TransactionOrder] = Field(default_factory=list)
    """Orders the transaction refers to."""
    lot_numbers: list[str] = Field(default_factory=list, max_length=1000)
    """Lot numbers of the goods (up to 1000)."""
    delivery_terms: str | None = None
    """Delivery terms, for example an Incoterms code."""
    contract_exchange_rate: Decimal | None = None
    """Exchange rate agreed in the contract."""
    contract_currency: str | None = None
    """Currency of the contract."""
    transports: list[TransactionTransport] = Field(default_factory=list, max_length=20)
    """Transport legs (up to 20)."""
    intermediary_entity: bool = False
    """Marks a transaction through an intermediary entity in a triangular transaction."""

    @field_validator("contract_currency")
    @classmethod
    def validate_contract_currency(cls, value: str | None) -> str | None:
        """Normalize the contract currency to uppercase and check it.

        Args:
            value: Currency code, or ``None``.

        Returns:
            The uppercase three-letter currency code, or ``None``.

        Raises:
            ValueError: If the value is not three letters or is ``PLN``.
        """
        if value is None:
            return None

        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{3}", normalized) is None:
            raise ValueError("contract_currency must be a 3-letter ISO code")
        if normalized == "PLN":
            raise ValueError("contract_currency cannot be PLN")
        return normalized

    @model_validator(mode="after")
    def validate_contract_currency_pair(self) -> Self:
        """Require the contract exchange rate and currency together.

        Returns:
            The validated conditions.

        Raises:
            ValueError: If only one of ``contract_exchange_rate`` and ``contract_currency`` is set.
        """
        has_exchange_rate = self.contract_exchange_rate is not None
        has_currency = self.contract_currency is not None
        if has_exchange_rate != has_currency:
            raise ValueError(
                "contract_exchange_rate and contract_currency must be provided together"
            )
        return self
