from polyfactory import BaseFactory

from ksef2.domain.models import testdata as domain_testdata
from ksef2.infra.mappers.testdata import to_spec
from ksef2.infra.schema.api.supp import testdata as supp


class TestTestDataMapper:
    def test_to_spec_string_values(self) -> None:
        assert to_spec("enforcement_authority") == "EnforcementAuthority"
        assert to_spec("invoice_write") == "InvoiceWrite"
        assert (
            to_spec(domain_testdata.AuthContextIdentifierTypeEnum.PEPPOL_ID)
            == "PeppolId"
        )

    def test_to_spec_create_subject_request(
        self,
        domain_td_create_subject_req: BaseFactory[domain_testdata.CreateSubjectRequest],
    ) -> None:
        request = domain_td_create_subject_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.CreateSubjectRequest)
        assert result.subjectNip == request.subject_nip
        assert result.subjectType == "EnforcementAuthority"
        assert result.subunits is not None
        assert request.subunits is not None
        assert result.subunits[0].subjectNip == request.subunits[0].subject_nip

    def test_to_spec_delete_subject_request(
        self,
        domain_td_delete_subject_req: BaseFactory[domain_testdata.DeleteSubjectRequest],
    ) -> None:
        request = domain_td_delete_subject_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.DeleteSubjectRequest)
        assert result.subjectNip == request.subject_nip

    def test_to_spec_create_person_request(
        self,
        domain_td_create_person_req: BaseFactory[domain_testdata.CreatePersonRequest],
    ) -> None:
        request = domain_td_create_person_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.CreatePersonRequest)
        assert result.nip == request.nip
        assert result.pesel == request.pesel
        assert result.isBailiff == request.is_bailiff

    def test_to_spec_delete_person_request(
        self,
        domain_td_delete_person_req: BaseFactory[domain_testdata.DeletePersonRequest],
    ) -> None:
        request = domain_td_delete_person_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.DeletePersonRequest)
        assert result.nip == request.nip

    def test_to_spec_grant_permissions_request(
        self,
        domain_td_grant_permissions_req: BaseFactory[
            domain_testdata.GrantPermissionsRequest
        ],
    ) -> None:
        request = domain_td_grant_permissions_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.GrantPermissionsRequest)
        assert result.contextIdentifier.type == "Nip"
        assert result.authorizedIdentifier.value == request.grant_to.value
        assert result.permissions[0].permissionType == "InvoiceRead"

    def test_to_spec_revoke_permissions_request(
        self,
        domain_td_revoke_permissions_req: BaseFactory[
            domain_testdata.RevokePermissionsRequest
        ],
    ) -> None:
        request = domain_td_revoke_permissions_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.RevokePermissionsRequest)
        assert result.contextIdentifier.value == request.in_context_of.value
        assert result.authorizedIdentifier.value == request.revoke_from.value

    def test_to_spec_enable_attachments_request(
        self,
        domain_td_enable_attachments_req: BaseFactory[
            domain_testdata.EnableAttachmentsRequest
        ],
    ) -> None:
        request = domain_td_enable_attachments_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.EnableAttachmentsRequest)
        assert result.nip == request.nip

    def test_to_spec_revoke_attachments_request(
        self,
        domain_td_revoke_attachments_req: BaseFactory[
            domain_testdata.RevokeAttachmentsRequest
        ],
    ) -> None:
        request = domain_td_revoke_attachments_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.RevokeAttachmentsRequest)
        assert result.nip == request.nip
        assert result.expectedEndDate == request.expected_end_date

    def test_to_spec_block_context_request(
        self,
        domain_td_block_context_req: BaseFactory[domain_testdata.BlockContextRequest],
    ) -> None:
        request = domain_td_block_context_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.BlockContextRequest)
        assert result.contextIdentifier.type == "Nip"
        assert result.contextIdentifier.value == request.context.value

    def test_to_spec_unblock_context_request(
        self,
        domain_td_unblock_context_req: BaseFactory[
            domain_testdata.UnblockContextRequest
        ],
    ) -> None:
        request = domain_td_unblock_context_req.build()

        result = to_spec(request)

        assert isinstance(result, supp.UnblockContextRequest)
        assert result.contextIdentifier.type == "Nip"
        assert result.contextIdentifier.value == request.context.value
