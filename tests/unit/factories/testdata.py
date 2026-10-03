from ksef2._domain.models import testdata as domain_testdata
from ksef2._infra.schema.api.supp.testdata import (
    BlockContextRequest,
    CreatePersonRequest,
    CreateSubjectRequest,
    DeletePersonRequest,
    DeleteSubjectRequest,
    EnableAttachmentsRequest,
    GrantPermissionsRequest,
    RevokeAttachmentsRequest,
    RevokePermissionsRequest,
    UnblockContextRequest,
)
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture


@register_fixture(name="domain_td_subunit")
class DomainSubUnitFactory(ModelFactory[domain_testdata.SubUnit]):
    subject_nip: str = "1234567890"
    description: str = "Subunit description"


@register_fixture(name="domain_td_identifier")
class DomainIdentifierFactory(ModelFactory[domain_testdata.Identifier]):
    type: str = "nip"
    value: str = "1234567890"


@register_fixture(name="domain_td_auth_context_identifier")
class DomainAuthContextIdentifierFactory(
    ModelFactory[domain_testdata.AuthContextIdentifier]
):
    type: str = "nip"
    value: str = "1234567890"


@register_fixture(name="domain_td_permission")
class DomainPermissionFactory(ModelFactory[domain_testdata.Permission]):
    type: str = "invoice_read"
    description: str = "Read invoices"


@register_fixture(name="domain_td_create_subject_req")
class DomainCreateSubjectRequestFactory(
    ModelFactory[domain_testdata.CreateSubjectRequest]
):
    subject_nip: str = "1234567890"
    subject_type: str = "enforcement_authority"
    description: str = "Test subject"

    @classmethod
    def subunits(cls) -> list[domain_testdata.SubUnit]:
        return [DomainSubUnitFactory.build()]


@register_fixture(name="domain_td_delete_subject_req")
class DomainDeleteSubjectRequestFactory(
    ModelFactory[domain_testdata.DeleteSubjectRequest]
):
    subject_nip: str = "1234567890"


@register_fixture(name="domain_td_create_person_req")
class DomainCreatePersonRequestFactory(
    ModelFactory[domain_testdata.CreatePersonRequest]
):
    nip: str = "1234567890"
    pesel: str = "12345678901"
    description: str = "Test person"


@register_fixture(name="domain_td_delete_person_req")
class DomainDeletePersonRequestFactory(
    ModelFactory[domain_testdata.DeletePersonRequest]
):
    nip: str = "1234567890"


@register_fixture(name="domain_td_grant_permissions_req")
class DomainGrantPermissionsRequestFactory(
    ModelFactory[domain_testdata.GrantPermissionsRequest]
):
    grant_to: domain_testdata.Identifier = DomainIdentifierFactory.build()
    in_context_of: domain_testdata.Identifier = DomainIdentifierFactory.build(
        value="0987654321"
    )

    @classmethod
    def permissions(cls) -> list[domain_testdata.Permission]:
        return [DomainPermissionFactory.build()]


@register_fixture(name="domain_td_revoke_permissions_req")
class DomainRevokePermissionsRequestFactory(
    ModelFactory[domain_testdata.RevokePermissionsRequest]
):
    revoke_from: domain_testdata.Identifier = DomainIdentifierFactory.build()
    in_context_of: domain_testdata.Identifier = DomainIdentifierFactory.build(
        value="0987654321"
    )


@register_fixture(name="domain_td_enable_attachments_req")
class DomainEnableAttachmentsRequestFactory(
    ModelFactory[domain_testdata.EnableAttachmentsRequest]
):
    nip: str = "1234567890"


@register_fixture(name="domain_td_revoke_attachments_req")
class DomainRevokeAttachmentsRequestFactory(
    ModelFactory[domain_testdata.RevokeAttachmentsRequest]
):
    nip: str = "1234567890"


@register_fixture(name="domain_td_block_context_req")
class DomainBlockContextRequestFactory(
    ModelFactory[domain_testdata.BlockContextRequest]
):
    context: domain_testdata.AuthContextIdentifier = (
        DomainAuthContextIdentifierFactory.build()
    )


@register_fixture(name="domain_td_unblock_context_req")
class DomainUnblockContextRequestFactory(
    ModelFactory[domain_testdata.UnblockContextRequest]
):
    context: domain_testdata.AuthContextIdentifier = (
        DomainAuthContextIdentifierFactory.build()
    )


@register_fixture(name="td_create_subject_req")
class CreateSubjectRequestFactory(ModelFactory[CreateSubjectRequest]): ...


@register_fixture(name="td_delete_subject_req")
class DeleteSubjectRequestFactory(ModelFactory[DeleteSubjectRequest]): ...


@register_fixture(name="td_create_person_req")
class CreatePersonRequestFactory(ModelFactory[CreatePersonRequest]): ...


@register_fixture(name="td_delete_person_req")
class DeletePersonRequestFactory(ModelFactory[DeletePersonRequest]): ...


@register_fixture(name="td_grant_permissions_req")
class GrantPermissionsRequestFactory(ModelFactory[GrantPermissionsRequest]): ...


@register_fixture(name="td_revoke_permissions_req")
class RevokePermissionsRequestFactory(ModelFactory[RevokePermissionsRequest]): ...


@register_fixture(name="td_enable_attachments_req")
class EnableAttachmentsRequestFactory(ModelFactory[EnableAttachmentsRequest]): ...


@register_fixture(name="td_revoke_attachments_req")
class RevokeAttachmentsRequestFactory(ModelFactory[RevokeAttachmentsRequest]): ...


@register_fixture(name="td_block_context_req")
class BlockContextRequestFactory(ModelFactory[BlockContextRequest]): ...


@register_fixture(name="td_unblock_context_req")
class UnblockContextRequestFactory(ModelFactory[UnblockContextRequest]): ...
