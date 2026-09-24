from collections.abc import Callable
from enum import StrEnum

import pytest
from polyfactory import BaseFactory

from ksef2.domain.models import permissions as domain_permissions
from ksef2.infra.mappers.permissions.requests import (
    author_identifier_from_literal,
    author_identifier_type_from_enum,
    authorizing_entity_identifier_from_literal,
    authorization_permission_query_from_literal,
    context_identifier_from_literal,
    entity_context_identifier_from_literal,
    eu_query_permission_from_enum,
    eu_query_permission_from_literal,
    permission_state_from_enum,
    permission_state_from_literal,
    personal_permission_type_from_literal,
    person_permission_type_from_literal,
    person_query_type_from_enum,
    person_query_type_from_literal,
    query_to_spec,
    query_type_from_enum,
    query_type_from_literal,
)
from ksef2.infra.mappers.permissions.responses import (
    entity_from_spec,
    eu_entity_from_spec,
    person_from_spec,
    personal_from_spec,
    subordinate_roles_from_spec,
    subunit_from_spec,
)
from ksef2.infra.schema.api import spec


class TestPermissionsQueryRequestMapper:
    def test_maps_person_query_all_optional_identifiers(
        self,
        domain_perm_query_persons: BaseFactory[
            domain_permissions.PersonPermissionsQuery
        ],
    ) -> None:
        request = domain_perm_query_persons.build(
            query_type="granted_in_context",
            permission_types=["invoice_read", "subunit_manage"],
            permission_state="inactive",
            author_type="fingerprint",
            author_value="a" * 64,
            authorized_type="pesel",
            authorized_value="12345678901",
            context_type="internal_id",
            context_value="1234567890-12345",
            target_type="all_partners",
            target_value="1234567890",
        )

        output = query_to_spec(request)

        assert isinstance(output, spec.PersonPermissionsQueryRequest)
        assert (
            output.queryType
            == spec.PersonPermissionsQueryType.PermissionsGrantedInCurrentContext
        )
        assert output.authorIdentifier is not None
        assert (
            output.authorIdentifier.type
            == spec.PersonPermissionsAuthorIdentifierType.Fingerprint
        )
        assert output.authorizedIdentifier is not None
        assert (
            output.authorizedIdentifier.type
            == spec.CertificateSubjectIdentifierType.Pesel
        )
        assert output.contextIdentifier is not None
        assert (
            output.contextIdentifier.type
            == spec.PersonPermissionsContextIdentifierType.InternalId
        )
        assert output.targetIdentifier is not None
        assert (
            output.targetIdentifier.type
            == spec.PersonPermissionsTargetIdentifierType.AllPartners
        )
        assert output.permissionTypes == [
            spec.PersonPermissionScope.InvoiceRead,
            spec.PersonPermissionScope.SubunitManage,
        ]
        assert output.permissionState == spec.PermissionState.Inactive

    def test_maps_authorization_query_permissions(
        self,
        domain_perm_query_authorizations: BaseFactory[
            domain_permissions.AuthorizationPermissionsQuery
        ],
    ) -> None:
        request = domain_perm_query_authorizations.build(
            query_type="received",
            permission_types=["self_invoicing", "pef_invoicing"],
            authorizing_type="nip",
            authorizing_value="1234567890",
            authorized_type="peppol_id",
            authorized_value="1234567890",
        )

        output = query_to_spec(request)

        assert isinstance(output, spec.EntityAuthorizationPermissionsQueryRequest)
        assert output.queryType == spec.QueryType.Received
        assert output.authorizingIdentifier is not None
        assert output.authorizingIdentifier.value == "1234567890"
        assert output.authorizedIdentifier is not None
        assert (
            output.authorizedIdentifier.type
            == spec.EntityAuthorizationPermissionsSubjectIdentifierType.PeppolId
        )
        assert output.permissionTypes == [
            spec.InvoicePermissionType.SelfInvoicing,
            spec.InvoicePermissionType.PefInvoicing,
        ]

    def test_maps_entity_query_context_identifier(
        self,
        domain_perm_query_entities: BaseFactory[
            domain_permissions.EntityPermissionsQuery
        ],
    ) -> None:
        request = domain_perm_query_entities.build(
            context_type="internal_id",
            context_value="1234567890-12345",
        )

        output = query_to_spec(request)

        assert isinstance(output, spec.EntityPermissionsQueryRequest)
        assert output.contextIdentifier is not None
        assert (
            output.contextIdentifier.type
            == spec.EntityPermissionsContextIdentifierType.InternalId
        )
        assert output.contextIdentifier.value == "1234567890-12345"

    def test_maps_personal_query_vat_ue_permission(
        self,
        domain_perm_query_personal: BaseFactory[
            domain_permissions.PersonalPermissionsQuery
        ],
    ) -> None:
        request = domain_perm_query_personal.build(
            permission_types=[
                "vat_ue_manage",
                "collective_identifier_manage",
            ],
            permission_state="active",
            context_type="internal_id",
            context_value="1234567890-12345",
            target_type="nip",
            target_value="1234567890",
        )

        output = query_to_spec(request)

        assert isinstance(output, spec.PersonalPermissionsQueryRequest)
        assert output.permissionTypes == [
            spec.PersonalPermissionType.VatUeManage,
            spec.PersonalPermissionType.CollectiveIdentifierManage,
        ]
        assert output.contextIdentifier is not None
        assert (
            output.contextIdentifier.type
            == spec.PersonalPermissionsContextIdentifierType.InternalId
        )
        assert output.targetIdentifier is not None
        assert (
            output.targetIdentifier.type
            == spec.PersonalPermissionsTargetIdentifierType.Nip
        )
        assert output.permissionState == spec.PermissionState.Active

    @pytest.mark.parametrize(
        ("func", "value"),
        [
            (author_identifier_from_literal, "internal_id"),
            (authorizing_entity_identifier_from_literal, "peppol_id"),
            (authorization_permission_query_from_literal, "invoice_read"),
            (context_identifier_from_literal, "all_partners"),
            (entity_context_identifier_from_literal, "all_partners"),
            (eu_query_permission_from_literal, "credentials_manage"),
            (permission_state_from_literal, "pending"),
            (person_permission_type_from_literal, "vat_ue_manage"),
            (personal_permission_type_from_literal, "pef_invoice_write"),
            (person_query_type_from_literal, "received"),
            (query_type_from_literal, "in_context"),
        ],
    )
    def test_rejects_invalid_query_literal_inputs(
        self, func: Callable[[str], StrEnum], value: str
    ) -> None:
        with pytest.raises(ValueError):
            _ = func(value)

    @pytest.mark.parametrize(
        "enum_value",
        [
            domain_permissions.IdentifierTypeEnum.INTERNAL_ID,
            domain_permissions.IdentifierTypeEnum.ALL_PARTNERS,
            domain_permissions.IdentifierTypeEnum.PEPPOL_ID,
        ],
    )
    def test_rejects_invalid_author_identifier_enums(
        self, enum_value: domain_permissions.IdentifierTypeEnum
    ) -> None:
        with pytest.raises(ValueError):
            _ = author_identifier_type_from_enum(enum_value)

    @pytest.mark.parametrize(
        ("func", "enum_value"),
        [
            (
                eu_query_permission_from_enum,
                domain_permissions.EuEntityQueryPermissionTypeEnum.INTROSPECTION,
            ),
            (
                permission_state_from_enum,
                domain_permissions.PermissionStateEnum.ACTIVE,
            ),
            (
                person_query_type_from_enum,
                domain_permissions.PersonPermissionsQueryTypeEnum.IN_CONTEXT,
            ),
            (query_type_from_enum, domain_permissions.QueryTypeEnum.GRANTED),
        ],
    )
    def test_maps_valid_query_enums(
        self, func: Callable[[StrEnum], str], enum_value: StrEnum
    ) -> None:
        assert func(enum_value) is not None

    def test_omits_subordinate_identifier_when_query_is_empty(
        self,
        domain_perm_query_subordinate: BaseFactory[
            domain_permissions.SubordinateEntityRolesQuery
        ],
    ) -> None:
        request = domain_perm_query_subordinate.build(subordinate_nip=None)

        output = query_to_spec(request)

        assert isinstance(output, spec.SubordinateEntityRolesQueryRequest)
        assert output.subordinateEntityIdentifier is None

    def test_omits_subunit_identifier_when_query_is_empty(
        self,
        domain_perm_query_subunits: BaseFactory[
            domain_permissions.SubunitPermissionsQuery
        ],
    ) -> None:
        request = domain_perm_query_subunits.build(subunit_nip=None)

        output = query_to_spec(request)

        assert isinstance(output, spec.SubunitPermissionsQueryRequest)
        assert output.subunitIdentifier is None


class TestPermissionsQueryResponseMapper:
    def test_maps_collective_identifier_permission_scopes(
        self,
        perm_person_item: BaseFactory[spec.PersonPermission],
        perm_personal_permission_item: BaseFactory[spec.PersonalPermission],
    ) -> None:
        person = person_from_spec(
            perm_person_item.build(
                permissionScope=spec.PersonPermissionScope.CollectiveIdentifierManage
            )
        )
        personal = personal_from_spec(
            perm_personal_permission_item.build(
                permissionScope=spec.PersonalPermissionScope.CollectiveIdentifierManage
            )
        )

        assert person.permission_type == "collective_identifier_manage"
        assert personal.permission_type == "collective_identifier_manage"

    def test_maps_person_permission_item(
        self,
        perm_person_item: BaseFactory[spec.PersonPermission],
        perm_person_context_identifier: BaseFactory[
            spec.PersonPermissionsContextIdentifier
        ],
        perm_person_target_identifier: BaseFactory[
            spec.PersonPermissionsTargetIdentifier
        ],
        perm_subject_person_details: BaseFactory[spec.PermissionsSubjectPersonDetails],
        perm_subject_entity_details: BaseFactory[spec.PermissionsSubjectEntityDetails],
    ) -> None:
        mapped_input = perm_person_item.build(
            contextIdentifier=perm_person_context_identifier.build(),
            targetIdentifier=perm_person_target_identifier.build(
                type=spec.IndirectPermissionsTargetIdentifierType.AllPartners,
                value="1234567890",
            ),
            subjectPersonDetails=perm_subject_person_details.build(
                firstName="Jan",
                lastName="Kowalski",
            ),
            subjectEntityDetails=perm_subject_entity_details.build(
                fullName="Entity Name",
                address="Main Street 1",
            ),
        )

        output = person_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.PersonPermissionDetail)
        assert output.author_type == "nip"
        assert output.context_type == "internal_id"
        assert output.target_type == "all_partners"
        assert output.person_first_name == "Jan"
        assert output.entity_first_name == "Entity Name"
        assert output.entity_last_name == "Entity Name"

    def test_maps_person_permission_without_optional_values(
        self,
        perm_person_item: BaseFactory[spec.PersonPermission],
    ) -> None:
        mapped_input = perm_person_item.build(
            authorIdentifier=spec.PersonPermissionsAuthorIdentifier(
                type=spec.PersonPermissionsAuthorIdentifierType.System,
                value=None,
            ),
            authorizedIdentifier=spec.PersonPermissionsAuthorizedIdentifier(
                type=spec.CertificateSubjectIdentifierType.Nip,
                value="1234567890",
            ),
            contextIdentifier=None,
            targetIdentifier=spec.PersonPermissionsTargetIdentifier(
                type=spec.PersonPermissionsTargetIdentifierType.AllPartners,
                value=None,
            ),
            subjectPersonDetails=None,
            subjectEntityDetails=None,
        )

        output = person_from_spec(mapped_input)

        assert output.author_type is None
        assert output.author_value is None
        assert output.context_type is None
        assert output.target_type == "all_partners"
        assert output.target_value is None

    def test_maps_authorization_grant_item(
        self,
        perm_authorization_grant_item: BaseFactory[spec.EntityAuthorizationGrant],
        perm_subject_entity_by_identifier_details: BaseFactory[
            spec.PermissionsSubjectEntityByIdentifierDetails
        ],
    ) -> None:
        mapped_input = perm_authorization_grant_item.build(
            authorIdentifier=None,
            subjectEntityDetails=perm_subject_entity_by_identifier_details.build(
                fullName="Authorized Entity"
            ),
        )

        output = entity_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.AuthorizationGrantDetail)
        assert output.author_type is None
        assert output.entity_full_name == "Authorized Entity"
        assert output.authorization_scope == "self_invoicing"
        assert output.authorized_entity_type == "nip"

    def test_maps_entity_role_parent_identifier_to_domain_literal(
        self,
        perm_entity_role_item: BaseFactory[spec.EntityRole],
        perm_entity_role_parent_identifier: BaseFactory[
            spec.EntityRolesParentEntityIdentifier
        ],
    ) -> None:
        mapped_input = perm_entity_role_item.build(
            parentEntityIdentifier=perm_entity_role_parent_identifier.build(
                type=spec.EntityAuthorizationsAuthorizingEntityIdentifierType.Nip,
                value="1234567890",
            )
        )

        output = entity_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.EntityRole)
        assert output.parent_entity_id_type == "nip"
        assert output.parent_entity_id_value == "1234567890"

    def test_maps_entity_permission_item(
        self,
        perm_entity_permission_item: BaseFactory[spec.EntityPermissionItem],
    ) -> None:
        mapped_input = perm_entity_permission_item.build(
            contextIdentifier=spec.EntityPermissionsContextIdentifier(
                type=spec.EntityPermissionsContextIdentifierType.InternalId,
                value="1234567890-12345",
            ),
            permissionScope=spec.EntityPermissionItemScope.InvoiceWrite,
        )

        output = entity_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.EntityPermissionDetail)
        assert output.context_type == "internal_id"
        assert output.context_value == "1234567890-12345"
        assert output.permission_type == "invoice_write"
        assert output.can_delegate is True

    def test_maps_collective_identifier_entity_permission(
        self,
        perm_entity_permission_item: BaseFactory[spec.EntityPermissionItem],
    ) -> None:
        mapped_input = perm_entity_permission_item.build(
            permissionScope=spec.EntityPermissionItemScope.CollectiveIdentifierManage,
        )

        output = entity_from_spec(mapped_input)

        assert output.permission_type == "collective_identifier_manage"

    def test_maps_personal_permission_item(
        self,
        perm_personal_permission_item: BaseFactory[spec.PersonalPermission],
        perm_personal_context_identifier: BaseFactory[
            spec.PersonalPermissionsContextIdentifier
        ],
        perm_personal_authorized_identifier: BaseFactory[
            spec.PersonalPermissionsAuthorizedIdentifier
        ],
        perm_personal_target_identifier: BaseFactory[
            spec.PersonalPermissionsTargetIdentifier
        ],
        perm_subject_person_details: BaseFactory[spec.PermissionsSubjectPersonDetails],
        perm_subject_entity_details: BaseFactory[spec.PermissionsSubjectEntityDetails],
    ) -> None:
        mapped_input = perm_personal_permission_item.build(
            contextIdentifier=perm_personal_context_identifier.build(),
            authorizedIdentifier=perm_personal_authorized_identifier.build(
                type=spec.PersonalPermissionsAuthorizedIdentifierType.Nip,
                value="1234567890",
            ),
            targetIdentifier=perm_personal_target_identifier.build(
                type=spec.PersonalPermissionsTargetIdentifierType.Nip,
                value="1234567890",
            ),
            subjectPersonDetails=perm_subject_person_details.build(
                firstName="Jan",
                lastName="Kowalski",
            ),
            subjectEntityDetails=perm_subject_entity_details.build(
                fullName="Entity Name",
                address="Main Street 1",
            ),
        )

        output = personal_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.PersonalPermissionDetail)
        assert output.context_type == "internal_id"
        assert output.authorized_type == "nip"
        assert output.target_type == "nip"
        assert output.permission_type == "vat_ue_manage"
        assert output.subject_first_name == "Jan"
        assert output.entity_address == "Main Street 1"

    def test_maps_eu_entity_permission_with_subject_entity_details(
        self,
        perm_eu_entity_permission_item: BaseFactory[spec.EuEntityPermission],
    ) -> None:
        mapped_input = perm_eu_entity_permission_item.build(
            subjectPersonDetails=None,
            subjectEntityDetails=spec.PermissionsSubjectEntityByFingerprintDetails(
                subjectDetailsType=spec.EntitySubjectByFingerprintDetailsType.EntityByFingerprint,
                fullName="Entity Name",
                address="Main Street 1",
            ),
            euEntityDetails=None,
        )

        output = eu_entity_from_spec(mapped_input)

        assert output.subject_first_name is None
        assert output.entity_full_name == "Entity Name"
        assert output.entity_address == "Main Street 1"

    def test_maps_eu_entity_permission_with_eu_entity_fallback(
        self,
        perm_eu_entity_permission_item: BaseFactory[spec.EuEntityPermission],
        perm_eu_entity_details: BaseFactory[spec.PermissionsEuEntityDetails],
    ) -> None:
        mapped_input = perm_eu_entity_permission_item.build(
            subjectPersonDetails=None,
            subjectEntityDetails=None,
            euEntityDetails=perm_eu_entity_details.build(
                fullName="EU Context Entity",
                address="EU Street 2",
            ),
        )

        output = eu_entity_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.EuEntityPermission)
        assert output.author_type == "nip"
        assert output.entity_full_name == "EU Context Entity"
        assert output.entity_address == "EU Street 2"
        assert output.permission_type == "invoice_read"

    def test_maps_subordinate_role_item(
        self, perm_subordinate_role_item: BaseFactory[spec.SubordinateEntityRole]
    ) -> None:
        mapped_input = perm_subordinate_role_item.build()

        output = subordinate_roles_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.SubordinateEntityRoleDetail)
        assert output.subordinate_entity_type == "nip"
        assert output.role == "local_government_sub_unit"

    def test_maps_subunit_permission_item(
        self,
        perm_subunit_permission_item: BaseFactory[spec.SubunitPermission],
        perm_subject_person_details: BaseFactory[spec.PermissionsSubjectPersonDetails],
    ) -> None:
        mapped_input = perm_subunit_permission_item.build(
            subjectPersonDetails=perm_subject_person_details.build(
                firstName="Jan",
                lastName="Kowalski",
            )
        )

        output = subunit_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.SubunitPermission)
        assert output.author_type == "pesel"
        assert output.authorized_type == "nip"
        assert output.subunit_type == "internal_id"
        assert output.subunit_name == "Subunit A"
        assert output.subject_first_name == "Jan"
