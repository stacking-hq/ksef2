"""Local validation shared by authentication and permission requests."""

import re
import ksef2._errors as exceptions


_NIP_PATTERN = re.compile(r"[1-9]((\d[1-9])|([1-9]\d))\d{7}")


def _nip_value(nip: str | None, *, parameter: str, normalize: bool) -> str:
    if not isinstance(nip, str):
        raise exceptions.KSeFArgumentError(
            f"{parameter} must be a 10-digit Polish NIP.",
            hint="Pass a NIP matching the declared identifier type.",
        )
    if not normalize:
        return nip
    normalized = re.sub(r"[-\s]", "", nip.strip()).upper()
    return normalized[2:] if normalized.startswith("PL") else normalized


def validate_nip_pattern(nip: str | None, *, parameter: str = "nip") -> str:
    """Validate the OpenAPI NIP pattern without imposing a checksum."""
    value = _nip_value(nip, parameter=parameter, normalize=False)
    if _NIP_PATTERN.fullmatch(value) is None:
        raise exceptions.KSeFArgumentError(
            f"{parameter} must match the 10-digit OpenAPI NIP pattern.",
            hint="Pass 10 digits, starting with 1-9, with the next two digits not both zero.",
        )
    return value


def validate_nip_checksum(
    nip: str | None, *, parameter: str = "nip", normalize: bool = True
) -> str:
    """Keep the test-certificate NIP normalization and checksum checks."""
    value = _nip_value(nip, parameter=parameter, normalize=normalize)
    if re.fullmatch(r"[0-9]{10}", value) is None:
        raise exceptions.KSeFArgumentError(
            f"{parameter} must contain exactly 10 digits.",
            hint="Pass 10 digits; dashes and a leading PL prefix are accepted."
            if normalize
            else "Pass a 10-digit NIP.",
        )
    checksum = (
        sum(
            int(digit) * weight
            for digit, weight in zip(
                value[:9], (6, 5, 7, 2, 3, 4, 5, 6, 7), strict=True
            )
        )
        % 11
    )
    if checksum == 10 or checksum != int(value[9]):
        raise exceptions.KSeFArgumentError(
            f"{parameter} has an invalid checksum.",
            hint="Check the 10-digit NIP value.",
        )
    return value


def validate_pesel(pesel: str, *, parameter: str = "pesel") -> str:
    """Validate the 11 ASCII digits and checksum without imposing date rules."""
    if re.fullmatch(r"[0-9]{11}", pesel) is None:
        raise exceptions.KSeFArgumentError(
            f"{parameter} must contain exactly 11 digits for a PESEL.",
            hint='Pass an 11-digit PESEL for subject_type="pesel".',
        )
    checksum = (
        10
        - sum(
            int(digit) * weight
            for digit, weight in zip(
                pesel[:10], (1, 3, 7, 9, 1, 3, 7, 9, 1, 3), strict=True
            )
        )
        % 10
    ) % 10
    if checksum != int(pesel[-1]):
        raise exceptions.KSeFArgumentError(
            f"{parameter} has an invalid PESEL checksum.",
            hint="Check the 11-digit PESEL value and subject_type.",
        )
    return pesel


def require_nonempty(value: object, parameter: str) -> None:
    """Reject empty credentials, identifiers, and permission lists locally."""
    if not value or isinstance(value, str) and not value.strip():
        raise exceptions.KSeFArgumentError(
            f"{parameter} must not be empty.",
            hint=f"Pass a non-empty {parameter} value.",
        )


def validate_permission_identifiers(data: dict[str, object]) -> None:
    """Validate NIP/PESEL only where the caller declares that identifier type."""
    for prefix in (
        "subject",
        "context",
        "target",
        "author",
        "authorized",
        "authorizing",
    ):
        kind = data.get(f"{prefix}_type")
        parameter = f"{prefix}_value"
        value = data.get(parameter)
        if isinstance(value, str):
            if kind == "nip":
                _ = validate_nip_pattern(value, parameter=parameter)
            elif kind == "pesel":
                _ = validate_pesel(value, parameter=parameter)
