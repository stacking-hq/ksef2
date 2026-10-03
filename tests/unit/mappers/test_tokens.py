from polyfactory import BaseFactory

from ksef2._domain.models import tokens
from ksef2._infra.mappers.tokens.requests import to_spec
from ksef2._infra.mappers.tokens.responses import from_spec
from ksef2._infra.schema.api import spec
from tests.unit.factories.tokens import (
    DomainGenerateTokenRequestFactory,
    QueryTokensResponseItemFactory,
    TokenAuthorIdentifierFactory,
    TokenContextIdentifierFactory,
)


class TestTokensResponseMapper:
    # --- enum mappers ---

    def test_map_status_pending(self):
        assert from_spec(spec.AuthenticationTokenStatus.Pending) == "pending"

    def test_map_status_active(self):
        assert from_spec(spec.AuthenticationTokenStatus.Active) == "active"

    def test_map_status_revoking(self):
        assert from_spec(spec.AuthenticationTokenStatus.Revoking) == "revoking"

    def test_map_status_revoked(self):
        assert from_spec(spec.AuthenticationTokenStatus.Revoked) == "revoked"

    def test_map_status_failed(self):
        assert from_spec(spec.AuthenticationTokenStatus.Failed) == "failed"

    def test_map_permission_invoice_read(self):
        assert from_spec(spec.TokenPermissionType.InvoiceRead) == "invoice_read"

    def test_map_permission_invoice_write(self):
        assert from_spec(spec.TokenPermissionType.InvoiceWrite) == "invoice_write"

    def test_map_permission_credentials_read(self):
        assert from_spec(spec.TokenPermissionType.CredentialsRead) == "credentials_read"

    def test_map_permission_credentials_manage(self):
        assert (
            from_spec(spec.TokenPermissionType.CredentialsManage)
            == "credentials_manage"
        )

    def test_map_permission_subunit_manage(self):
        assert from_spec(spec.TokenPermissionType.SubunitManage) == "subunit_manage"

    def test_map_permission_enforcement_operations(self):
        assert (
            from_spec(spec.TokenPermissionType.EnforcementOperations)
            == "enforcement_operations"
        )

    def test_map_permission_collective_identifier_manage(self):
        assert (
            from_spec(spec.TokenPermissionType.CollectiveIdentifierManage)
            == "collective_identifier_manage"
        )

    def test_map_author_identifier_type_nip(self):
        assert from_spec(spec.TokenAuthorIdentifierType.Nip) == "nip"

    def test_map_author_identifier_type_pesel(self):
        assert from_spec(spec.TokenAuthorIdentifierType.Pesel) == "pesel"

    def test_map_author_identifier_type_fingerprint(self):
        assert from_spec(spec.TokenAuthorIdentifierType.Fingerprint) == "fingerprint"

    def test_map_context_identifier_type_nip(self):
        assert from_spec(spec.TokenContextIdentifierType.Nip) == "nip"

    def test_map_context_identifier_type_internal_id(self):
        assert from_spec(spec.TokenContextIdentifierType.InternalId) == "internal_id"

    def test_map_context_identifier_type_nip_vat_ue(self):
        assert from_spec(spec.TokenContextIdentifierType.NipVatUe) == "nip_vat_ue"

    def test_map_context_identifier_type_peppol_id(self):
        assert from_spec(spec.TokenContextIdentifierType.PeppolId) == "peppol_id"

    # --- composite model mappers ---

    def test_map_author_identifier(self):
        mapped_input = TokenAuthorIdentifierFactory.build()
        output = from_spec(mapped_input)

        assert isinstance(output, tokens.TokenAuthorIdentifier)
        assert output.type == from_spec(mapped_input.type)
        assert output.value == mapped_input.value

    def test_map_context_identifier(self):
        mapped_input = TokenContextIdentifierFactory.build()
        output = from_spec(mapped_input)

        assert isinstance(output, tokens.TokenContextIdentifier)
        assert output.type == from_spec(mapped_input.type)
        assert output.value == mapped_input.value

    def test_map_generate_token_response(
        self, token_generate_resp: BaseFactory[spec.GenerateTokenResponse]
    ):
        mapped_input = token_generate_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, tokens.GenerateTokenResponse)
        assert output.reference_number == mapped_input.referenceNumber
        assert output.token == mapped_input.token

    def test_map_token_status_response(
        self, token_status_resp: BaseFactory[spec.TokenStatusResponse]
    ):
        mapped_input = token_status_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, tokens.TokenStatusResponse)
        assert output.reference_number == mapped_input.referenceNumber
        assert output.status == from_spec(mapped_input.status)

    def test_map_query_tokens_response_item(self):
        mapped_input = QueryTokensResponseItemFactory.build()
        output = from_spec(mapped_input)

        assert isinstance(output, tokens.TokenInfo)
        assert output.reference_number == mapped_input.referenceNumber
        assert output.description == mapped_input.description
        assert output.date_created == mapped_input.dateCreated
        assert output.last_use_date == mapped_input.lastUseDate
        assert output.status == from_spec(mapped_input.status)
        assert output.status_details == mapped_input.statusDetails
        assert len(output.requested_permissions) == len(
            mapped_input.requestedPermissions
        )

    def test_map_query_tokens_response(
        self, token_list_resp: BaseFactory[spec.QueryTokensResponse]
    ):
        mapped_input = token_list_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, tokens.QueryTokensResponse)
        assert output.continuation_token == mapped_input.continuationToken
        assert len(output.tokens) == len(mapped_input.tokens)


class TestTokensRequestMapper:
    # --- enum mappers ---

    def test_to_spec_permission_invoice_read(self):
        assert to_spec("invoice_read") == spec.TokenPermissionType.InvoiceRead

    def test_to_spec_permission_invoice_write(self):
        assert to_spec("invoice_write") == spec.TokenPermissionType.InvoiceWrite

    def test_to_spec_permission_credentials_read(self):
        assert to_spec("credentials_read") == spec.TokenPermissionType.CredentialsRead

    def test_to_spec_permission_credentials_manage(self):
        assert (
            to_spec("credentials_manage") == spec.TokenPermissionType.CredentialsManage
        )

    def test_to_spec_permission_subunit_manage(self):
        assert to_spec("subunit_manage") == spec.TokenPermissionType.SubunitManage

    def test_to_spec_permission_enforcement_operations(self):
        assert (
            to_spec("enforcement_operations")
            == spec.TokenPermissionType.EnforcementOperations
        )

    def test_to_spec_permission_collective_identifier_manage(self):
        assert (
            to_spec("collective_identifier_manage")
            == spec.TokenPermissionType.CollectiveIdentifierManage
        )

    def test_to_spec_status_pending(self):
        assert to_spec("pending") == spec.AuthenticationTokenStatus.Pending

    def test_to_spec_status_active(self):
        assert to_spec("active") == spec.AuthenticationTokenStatus.Active

    def test_to_spec_status_revoking(self):
        assert to_spec("revoking") == spec.AuthenticationTokenStatus.Revoking

    def test_to_spec_status_revoked(self):
        assert to_spec("revoked") == spec.AuthenticationTokenStatus.Revoked

    def test_to_spec_status_failed(self):
        assert to_spec("failed") == spec.AuthenticationTokenStatus.Failed

    # --- composite model mappers ---

    def test_to_spec_generate_token_request(self):
        request = DomainGenerateTokenRequestFactory.build()
        output = to_spec(request)

        assert isinstance(output, spec.GenerateTokenRequest)
        assert output.description == request.description
        assert len(output.permissions) == len(request.permissions)
        for domain_perm, spec_perm in zip(
            request.permissions, output.permissions, strict=True
        ):
            assert spec_perm == to_spec(domain_perm)

    def test_to_spec_generate_token_request_multiple_permissions(self):
        request = DomainGenerateTokenRequestFactory.build(
            permissions=["invoice_read", "invoice_write", "credentials_read"]
        )
        output = to_spec(request)

        assert isinstance(output, spec.GenerateTokenRequest)
        assert len(output.permissions) == 3
        assert output.permissions[0] == spec.TokenPermissionType.InvoiceRead
        assert output.permissions[1] == spec.TokenPermissionType.InvoiceWrite
        assert output.permissions[2] == spec.TokenPermissionType.CredentialsRead

    def test_to_spec_unknown_string_raises(self):
        import pytest

        with pytest.raises(NotImplementedError, match="No mapper for string value"):
            _ = to_spec("unknown_value")  # pyright: ignore[reportArgumentType]
