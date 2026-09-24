"""Mappings from permission grant models to generated API schema payloads."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.permissions import (
    AuthorizationPermissionTypeEnum,
    GrantAuthorizationPermissionsRequest,
    GrantEntityPermissionsRequest,
    GrantEuEntityAdministrationRequest,
    GrantEuEntityPermissionsRequest,
    GrantIndirectPermissionsRequest,
    GrantPersonPermissionsRequest,
    GrantSubunitPermissionsRequest,
    IndirectPermissionTypeEnum,
    PersonPermissionTypeEnum,
)
from ksef2.infra.mappers.permissions.requests.shared import (
    indirect_target_identifier_from_literal,
)
from ksef2.infra.schema.api import spec


def authorization_permission_from_literal(
    value: str,
) -> spec.EntityAuthorizationPermissionType:
    match value:
        case "self_invoicing":
            return spec.EntityAuthorizationPermissionType.SelfInvoicing
        case "rr_invoicing":
            return spec.EntityAuthorizationPermissionType.RRInvoicing
        case "tax_representative":
            return spec.EntityAuthorizationPermissionType.TaxRepresentative
        case "pef_invoicing":
            return spec.EntityAuthorizationPermissionType.PefInvoicing
        case _:
            raise ValueError(f"Unknown authorization permission type: {value!r}")


def authorization_permission_from_enum(
    request: AuthorizationPermissionTypeEnum,
) -> spec.EntityAuthorizationPermissionType:
    match request:
        case AuthorizationPermissionTypeEnum.SELF_INVOICING:
            return spec.EntityAuthorizationPermissionType.SelfInvoicing
        case AuthorizationPermissionTypeEnum.RR_INVOICING:
            return spec.EntityAuthorizationPermissionType.RRInvoicing
        case AuthorizationPermissionTypeEnum.TAX_REPRESENTATIVE:
            return spec.EntityAuthorizationPermissionType.TaxRepresentative
        case AuthorizationPermissionTypeEnum.PEF_INVOICING:
            return spec.EntityAuthorizationPermissionType.PefInvoicing
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def authorization_subject_identifier_from_literal(
    value: str,
) -> spec.EntityAuthorizationPermissionsSubjectIdentifierType:
    match value:
        case "nip":
            return spec.EntityAuthorizationPermissionsSubjectIdentifierType.Nip
        case "peppol_id":
            return spec.EntityAuthorizationPermissionsSubjectIdentifierType.PeppolId
        case _:
            raise ValueError(
                f"Unknown authorization subject identifier type: {value!r}"
            )


def entity_permission_from_literal(value: str) -> spec.EntityPermissionType:
    match value:
        case "invoice_read":
            return spec.EntityPermissionType.InvoiceRead
        case "invoice_write":
            return spec.EntityPermissionType.InvoiceWrite
        case "collective_identifier_manage":
            return spec.EntityPermissionType.CollectiveIdentifierManage
        case _:
            raise ValueError(f"Unknown entity permission type: {value!r}")


def eu_admin_context_identifier_from_literal(
    value: str,
) -> spec.EuEntityAdministrationPermissionsContextIdentifierType:
    match value:
        case "nip_vat_ue":
            return spec.EuEntityAdministrationPermissionsContextIdentifierType.NipVatUe
        case _:
            raise ValueError(f"Unknown EU admin context type: {value!r}")


def indirect_permission_from_literal(value: str) -> spec.IndirectPermissionType:
    match value:
        case "invoice_read":
            return spec.IndirectPermissionType.InvoiceRead
        case "invoice_write":
            return spec.IndirectPermissionType.InvoiceWrite
        case "collective_identifier_manage":
            return spec.IndirectPermissionType.CollectiveIdentifierManage
        case _:
            raise ValueError(f"Unknown indirect permission type: {value!r}")


def indirect_permission_from_enum(
    request: IndirectPermissionTypeEnum,
) -> spec.IndirectPermissionType:
    match request:
        case IndirectPermissionTypeEnum.INVOICE_READ:
            return spec.IndirectPermissionType.InvoiceRead
        case IndirectPermissionTypeEnum.INVOICE_WRITE:
            return spec.IndirectPermissionType.InvoiceWrite
        case IndirectPermissionTypeEnum.COLLECTIVE_IDENTIFIER_MANAGE:
            return spec.IndirectPermissionType.CollectiveIdentifierManage
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def person_permission_scope_from_literal(value: str) -> spec.PersonPermissionScope:
    match value:
        case "invoice_read":
            return spec.PersonPermissionScope.InvoiceRead
        case "invoice_write":
            return spec.PersonPermissionScope.InvoiceWrite
        case "introspection":
            return spec.PersonPermissionScope.Introspection
        case "credentials_read":
            return spec.PersonPermissionScope.CredentialsRead
        case "credentials_manage":
            return spec.PersonPermissionScope.CredentialsManage
        case "enforcement_operations":
            return spec.PersonPermissionScope.EnforcementOperations
        case "subunit_manage":
            return spec.PersonPermissionScope.SubunitManage
        case "collective_identifier_manage":
            return spec.PersonPermissionScope.CollectiveIdentifierManage
        case _:
            raise ValueError(f"Unknown person permission type: {value!r}")


def person_permission_type_from_literal(value: str) -> spec.PersonPermissionType:
    match value:
        case "invoice_read":
            return spec.PersonPermissionType.InvoiceRead
        case "invoice_write":
            return spec.PersonPermissionType.InvoiceWrite
        case "introspection":
            return spec.PersonPermissionType.Introspection
        case "credentials_read":
            return spec.PersonPermissionType.CredentialsRead
        case "credentials_manage":
            return spec.PersonPermissionType.CredentialsManage
        case "enforcement_operations":
            return spec.PersonPermissionType.EnforcementOperations
        case "subunit_manage":
            return spec.PersonPermissionType.SubunitManage
        case "collective_identifier_manage":
            return spec.PersonPermissionType.CollectiveIdentifierManage
        case _:
            raise ValueError(f"Unknown person permission type: {value!r}")


def person_permission_scope_from_enum(
    request: PersonPermissionTypeEnum,
) -> spec.PersonPermissionScope:
    match request:
        case PersonPermissionTypeEnum.INVOICE_READ:
            return spec.PersonPermissionScope.InvoiceRead
        case PersonPermissionTypeEnum.INVOICE_WRITE:
            return spec.PersonPermissionScope.InvoiceWrite
        case PersonPermissionTypeEnum.INTROSPECTION:
            return spec.PersonPermissionScope.Introspection
        case PersonPermissionTypeEnum.CREDENTIALS_READ:
            return spec.PersonPermissionScope.CredentialsRead
        case PersonPermissionTypeEnum.CREDENTIALS_MANAGE:
            return spec.PersonPermissionScope.CredentialsManage
        case PersonPermissionTypeEnum.ENFORCEMENT_OPERATIONS:
            return spec.PersonPermissionScope.EnforcementOperations
        case PersonPermissionTypeEnum.SUBUNIT_MANAGE:
            return spec.PersonPermissionScope.SubunitManage
        case PersonPermissionTypeEnum.COLLECTIVE_IDENTIFIER_MANAGE:
            return spec.PersonPermissionScope.CollectiveIdentifierManage
        case PersonPermissionTypeEnum.PEF_INVOICE_WRITE:
            raise ValueError(
                "Permission 'pef_invoice_write' is not valid for person grants"
            )
        case PersonPermissionTypeEnum.VAT_UE_MANAGE:
            raise ValueError(
                "Permission 'vat_ue_manage' is not valid for person grants"
            )
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def subunit_context_identifier_from_literal(
    value: str,
) -> spec.SubunitPermissionsContextIdentifierType:
    match value:
        case "nip":
            return spec.SubunitPermissionsContextIdentifierType.Nip
        case "internal_id":
            return spec.SubunitPermissionsContextIdentifierType.InternalId
        case _:
            raise ValueError(f"Unknown subunit identifier type: {value!r}")


def person_subject_identifier_from_literal(
    value: str,
) -> spec.PersonPermissionsSubjectIdentifierType:
    match value:
        case "nip":
            return spec.PersonPermissionsSubjectIdentifierType.Nip
        case "pesel":
            return spec.PersonPermissionsSubjectIdentifierType.Pesel
        case "fingerprint":
            return spec.PersonPermissionsSubjectIdentifierType.Fingerprint
        case _:
            raise ValueError(f"Unknown person subject identifier type: {value!r}")


def indirect_subject_identifier_from_literal(
    value: str,
) -> spec.IndirectPermissionsSubjectIdentifierType:
    match value:
        case "nip":
            return spec.IndirectPermissionsSubjectIdentifierType.Nip
        case "pesel":
            return spec.IndirectPermissionsSubjectIdentifierType.Pesel
        case "fingerprint":
            return spec.IndirectPermissionsSubjectIdentifierType.Fingerprint
        case _:
            raise ValueError(f"Unknown indirect subject identifier type: {value!r}")


def subunit_subject_identifier_from_literal(
    value: str,
) -> spec.SubunitPermissionsSubjectIdentifierType:
    match value:
        case "nip":
            return spec.SubunitPermissionsSubjectIdentifierType.Nip
        case "pesel":
            return spec.SubunitPermissionsSubjectIdentifierType.Pesel
        case "fingerprint":
            return spec.SubunitPermissionsSubjectIdentifierType.Fingerprint
        case _:
            raise ValueError(f"Unknown subunit subject identifier type: {value!r}")


def eu_entity_permission_from_literal(value: str) -> spec.EuEntityPermissionType:
    match value:
        case "invoice_read":
            return spec.EuEntityPermissionType.InvoiceRead
        case "invoice_write":
            return spec.EuEntityPermissionType.InvoiceWrite
        case _:
            raise ValueError(f"Unknown EU entity permission type: {value!r}")


@overload
def to_spec(
    request: GrantPersonPermissionsRequest,
) -> spec.PersonPermissionsGrantRequest: ...


@overload
def to_spec(
    request: GrantEntityPermissionsRequest,
) -> spec.EntityPermissionsGrantRequest: ...


@overload
def to_spec(
    request: GrantAuthorizationPermissionsRequest,
) -> spec.EntityAuthorizationPermissionsGrantRequest: ...


@overload
def to_spec(
    request: GrantIndirectPermissionsRequest,
) -> spec.IndirectPermissionsGrantRequest: ...


@overload
def to_spec(
    request: GrantSubunitPermissionsRequest,
) -> spec.SubunitPermissionsGrantRequest: ...


@overload
def to_spec(
    request: GrantEuEntityPermissionsRequest,
) -> spec.EuEntityPermissionsGrantRequest: ...


@overload
def to_spec(
    request: GrantEuEntityAdministrationRequest,
) -> spec.EuEntityAdministrationPermissionsGrantRequest: ...


def to_spec(request: BaseModel | Enum) -> object:
    """Convert a permission grant model into the schema payload expected by KSeF."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: GrantPersonPermissionsRequest) -> spec.PersonPermissionsGrantRequest:
    return spec.PersonPermissionsGrantRequest(
        subjectIdentifier=spec.PersonPermissionsSubjectIdentifier(
            type=person_subject_identifier_from_literal(request.subject_type),
            value=request.subject_value,
        ),
        permissions=[
            person_permission_type_from_literal(p) for p in request.permissions
        ],
        description=request.description,
        subjectDetails=spec.PersonPermissionSubjectDetails(
            subjectDetailsType=spec.PersonPermissionSubjectDetailsType.PersonByIdentifier,
            personById=spec.PersonDetails(
                firstName=request.first_name,
                lastName=request.last_name,
            ),
        ),
    )


@_to_spec.register
def _(request: GrantEntityPermissionsRequest) -> spec.EntityPermissionsGrantRequest:
    return spec.EntityPermissionsGrantRequest(
        subjectIdentifier=spec.EntityPermissionsSubjectIdentifier(
            type=spec.EntityPermissionsSubjectIdentifierType.Nip,
            value=request.subject_value,
        ),
        permissions=[
            spec.EntityPermission(
                type=entity_permission_from_literal(p.type),
                canDelegate=p.can_delegate,
            )
            for p in request.permissions
        ],
        description=request.description,
        subjectDetails=spec.EntityDetails(
            fullName=request.entity_name,
        ),
    )


@_to_spec.register
def _(
    request: GrantAuthorizationPermissionsRequest,
) -> spec.EntityAuthorizationPermissionsGrantRequest:
    return spec.EntityAuthorizationPermissionsGrantRequest(
        subjectIdentifier=spec.EntityAuthorizationPermissionsSubjectIdentifier(
            type=authorization_subject_identifier_from_literal(request.subject_type),
            value=request.subject_value,
        ),
        permission=authorization_permission_from_literal(request.permission),
        description=request.description,
        subjectDetails=spec.EntityDetails(
            fullName=request.entity_name,
        ),
    )


@_to_spec.register
def _(request: GrantIndirectPermissionsRequest) -> spec.IndirectPermissionsGrantRequest:
    target_id = None
    if request.target_type and request.target_value:
        target_id = spec.IndirectPermissionsTargetIdentifier(
            type=indirect_target_identifier_from_literal(request.target_type),
            value=request.target_value,
        )

    return spec.IndirectPermissionsGrantRequest(
        subjectIdentifier=spec.IndirectPermissionsSubjectIdentifier(
            type=indirect_subject_identifier_from_literal(request.subject_type),
            value=request.subject_value,
        ),
        targetIdentifier=target_id,
        permissions=[indirect_permission_from_literal(p) for p in request.permissions],
        description=request.description,
        subjectDetails=spec.PersonPermissionSubjectDetails(
            subjectDetailsType=spec.PersonPermissionSubjectDetailsType.PersonByIdentifier,
            personById=spec.PersonDetails(
                firstName=request.first_name,
                lastName=request.last_name,
            ),
        ),
    )


@_to_spec.register
def _(request: GrantSubunitPermissionsRequest) -> spec.SubunitPermissionsGrantRequest:
    return spec.SubunitPermissionsGrantRequest(
        subjectIdentifier=spec.SubunitPermissionsSubjectIdentifier(
            type=subunit_subject_identifier_from_literal(request.subject_type),
            value=request.subject_value,
        ),
        contextIdentifier=spec.SubunitPermissionsContextIdentifier(
            type=subunit_context_identifier_from_literal(request.context_type),
            value=request.context_value,
        ),
        description=request.description,
        subunitName=request.subunit_name,
        subjectDetails=spec.PersonPermissionSubjectDetails(
            subjectDetailsType=spec.PersonPermissionSubjectDetailsType.PersonByIdentifier,
            personById=spec.PersonDetails(
                firstName=request.first_name,
                lastName=request.last_name,
            ),
        ),
    )


@_to_spec.register
def _(request: GrantEuEntityPermissionsRequest) -> spec.EuEntityPermissionsGrantRequest:
    return spec.EuEntityPermissionsGrantRequest(
        subjectIdentifier=spec.EuEntityPermissionsSubjectIdentifier(
            type=spec.EuEntityPermissionsSubjectIdentifierType.Fingerprint,
            value=request.subject_value,
        ),
        permissions=[eu_entity_permission_from_literal(p) for p in request.permissions],
        description=request.description,
        subjectDetails=spec.EuEntityPermissionSubjectDetails(
            subjectDetailsType=spec.EuEntityPermissionSubjectDetailsType.EntityByFingerprint,
        ),
    )


@_to_spec.register
def _(
    request: GrantEuEntityAdministrationRequest,
) -> spec.EuEntityAdministrationPermissionsGrantRequest:
    return spec.EuEntityAdministrationPermissionsGrantRequest(
        subjectIdentifier=spec.EuEntityAdministrationPermissionsSubjectIdentifier(
            type=spec.EuEntityAdministrationPermissionsSubjectIdentifierType.Fingerprint,
            value=request.subject_value,
        ),
        contextIdentifier=spec.EuEntityAdministrationPermissionsContextIdentifier(
            type=eu_admin_context_identifier_from_literal(request.context_type),
            value=request.context_value,
        ),
        description=request.description,
        euEntityName=request.eu_entity_name,
        subjectDetails=spec.EuEntityPermissionSubjectDetails(
            subjectDetailsType=spec.EuEntityPermissionSubjectDetailsType.EntityByFingerprint,
        ),
        euEntityDetails=spec.EuEntityDetails(
            fullName=request.eu_entity_name,
            address="",
        ),
    )
