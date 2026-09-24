from collections.abc import Callable
from enum import StrEnum

import pytest
from polyfactory import BaseFactory

from ksef2.domain.models import permissions as domain_permissions
from ksef2.infra.mappers.permissions.requests import (
    authorization_permission_from_enum,
    authorization_permission_from_literal,
    authorization_subject_identifier_from_literal,
    cert_subject_identifier_from_literal,
    entity_permission_from_literal,
    eu_admin_context_identifier_from_literal,
    grant_to_spec,
    indirect_permission_from_enum,
    indirect_permission_from_literal,
    indirect_target_identifier_from_literal,
    person_permission_scope_from_enum,
    person_permission_scope_from_literal,
    subunit_context_identifier_from_literal,
)
from ksef2.infra.mappers.permissions.responses import grant_from_spec
from ksef2.infra.schema.api import spec
from tests.unit.factories.permissions import (
    DomainGrantEuEntityAdministrationRequestFactory,
    DomainGrantIndirectPermissionsRequestFactory,
    DomainGrantPersonPermissionsRequestFactory,
)


class TestPermissionsGrantRequestMapper:
    def test_maps_collective_identifier_permissions(self) -> None:
        assert (
            entity_permission_from_literal("collective_identifier_manage")
            == spec.EntityPermissionType.CollectiveIdentifierManage
        )
        assert (
            indirect_permission_from_literal("collective_identifier_manage")
            == spec.IndirectPermissionType.CollectiveIdentifierManage
        )
        assert (
            indirect_permission_from_enum(
                domain_permissions.IndirectPermissionTypeEnum.COLLECTIVE_IDENTIFIER_MANAGE
            )
            == spec.IndirectPermissionType.CollectiveIdentifierManage
        )

    def test_maps_grant_person_request_payload(self) -> None:
        request = DomainGrantPersonPermissionsRequestFactory.build(
            permissions=["invoice_read", "credentials_manage"],
        )

        output = grant_to_spec(request)

        assert isinstance(output, spec.PersonPermissionsGrantRequest)
        assert output.subjectIdentifier.value == request.subject_value

        assert output.subjectDetails.personById is not None
        assert output.subjectDetails.personById.firstName == request.first_name
        assert output.subjectDetails.personById.lastName == request.last_name

    def test_omits_indirect_target_identifier_when_not_provided(self) -> None:
        request = DomainGrantIndirectPermissionsRequestFactory.build(
            target_type=None,
            target_value=None,
        )

        output = grant_to_spec(request)

        assert isinstance(output, spec.IndirectPermissionsGrantRequest)
        assert output.targetIdentifier is None

    def test_maps_indirect_target_identifier_when_provided(self) -> None:
        request = DomainGrantIndirectPermissionsRequestFactory.build(
            target_type="all_partners",
            target_value="1234567890",
        )

        output = grant_to_spec(request)

        assert isinstance(output, spec.IndirectPermissionsGrantRequest)
        assert output.targetIdentifier is not None
        assert (
            output.targetIdentifier.type
            == spec.IndirectPermissionsTargetIdentifierType.AllPartners
        )
        assert output.targetIdentifier.value == request.target_value

    def test_maps_eu_entity_administration_details(self) -> None:
        request = DomainGrantEuEntityAdministrationRequestFactory.build(
            eu_entity_name="Example EU Entity",
        )

        output = grant_to_spec(request)

        assert isinstance(output, spec.EuEntityAdministrationPermissionsGrantRequest)
        assert output.euEntityName == "Example EU Entity"
        assert output.euEntityDetails.fullName == "Example EU Entity"

    @pytest.mark.parametrize(
        ("func", "value"),
        [
            (cert_subject_identifier_from_literal, "system"),
            (authorization_permission_from_literal, "invoice_read"),
            (authorization_subject_identifier_from_literal, "pesel"),
            (entity_permission_from_literal, "credentials_manage"),
            (eu_admin_context_identifier_from_literal, "nip"),
            (indirect_permission_from_literal, "introspection"),
            (indirect_target_identifier_from_literal, "fingerprint"),
            (person_permission_scope_from_literal, "vat_ue_manage"),
            (subunit_context_identifier_from_literal, "pesel"),
        ],
    )
    def test_rejects_invalid_literal_inputs(
        self, func: Callable[[str], StrEnum], value: str
    ) -> None:
        with pytest.raises(ValueError):
            _ = func(value)

    @pytest.mark.parametrize(
        ("func", "enum_value"),
        [
            (
                authorization_permission_from_enum,
                domain_permissions.AuthorizationPermissionTypeEnum.SELF_INVOICING,
            ),
            (
                indirect_permission_from_enum,
                domain_permissions.IndirectPermissionTypeEnum.INVOICE_READ,
            ),
            (
                person_permission_scope_from_enum,
                domain_permissions.PersonPermissionTypeEnum.COLLECTIVE_IDENTIFIER_MANAGE,
            ),
        ],
    )
    def test_maps_enum_inputs(
        self, func: Callable[[StrEnum], str], enum_value: StrEnum
    ) -> None:
        assert func(enum_value) is not None

    @pytest.mark.parametrize(
        "enum_value",
        [
            domain_permissions.PersonPermissionTypeEnum.PEF_INVOICE_WRITE,
            domain_permissions.PersonPermissionTypeEnum.VAT_UE_MANAGE,
        ],
    )
    def test_rejects_invalid_person_grant_permission_enums(
        self, enum_value: domain_permissions.PersonPermissionTypeEnum
    ) -> None:
        with pytest.raises(ValueError):
            _ = person_permission_scope_from_enum(enum_value)


class TestPermissionsGrantResponseMapper:
    def test_maps_operation_response(
        self, perm_op_resp: BaseFactory[spec.PermissionsOperationResponse]
    ) -> None:
        mapped_input = perm_op_resp.build()

        output = grant_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.GrantPermissionsResponse)
        assert output.reference_number == mapped_input.referenceNumber

    def test_maps_operation_status_response(
        self, perm_op_status_resp: BaseFactory[spec.PermissionsOperationStatusResponse]
    ) -> None:
        mapped_input = perm_op_status_resp.build()

        output = grant_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.PermissionOperationStatusResponse)
        assert output.status.code == mapped_input.status.code
        assert output.status.description == mapped_input.status.description

    def test_maps_attachment_status_response(
        self,
        perm_attachment_status_resp: BaseFactory[
            spec.CheckAttachmentPermissionStatusResponse
        ],
    ) -> None:
        mapped_input = perm_attachment_status_resp.build(isAttachmentAllowed=None)

        output = grant_from_spec(mapped_input)

        assert isinstance(output, domain_permissions.AttachmentPermissionStatus)
        assert output.is_attachment_allowed is False
        assert output.revoked_date == mapped_input.revokedDate
