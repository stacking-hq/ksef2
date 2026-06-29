from ksef2.infra.schema.api import spec


def cert_subject_identifier_from_literal(
    value: str,
) -> spec.CertificateSubjectIdentifierType:
    match value:
        case "nip":
            return spec.CertificateSubjectIdentifierType.Nip
        case "pesel":
            return spec.CertificateSubjectIdentifierType.Pesel
        case "fingerprint":
            return spec.CertificateSubjectIdentifierType.Fingerprint
        case _:
            raise ValueError(f"Unknown certificate subject identifier type: {value!r}")


def indirect_target_identifier_from_literal(
    value: str,
) -> spec.IndirectPermissionsTargetIdentifierType:
    match value:
        case "nip":
            return spec.IndirectPermissionsTargetIdentifierType.Nip
        case "all_partners":
            return spec.IndirectPermissionsTargetIdentifierType.AllPartners
        case "internal_id":
            return spec.IndirectPermissionsTargetIdentifierType.InternalId
        case _:
            raise ValueError(f"Unknown indirect target identifier type: {value!r}")
