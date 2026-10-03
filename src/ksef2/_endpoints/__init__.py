from dataclasses import dataclass

from ksef2._endpoints import (
    peppol as peppol,
    testdata as testdata,
    limits as limits,
    tokens as tokens,
    encryption as encryption,
    auth as auth,
    invoices as invoices,
    collective_identifiers as collective_identifiers,
    certificates as certificates,
    session as session,
)
from ksef2._core import routes


@dataclass(frozen=True)
class EndpointRef:
    method: str
    url: str


__auth_endpoints__ = [
    EndpointRef("POST", routes.AuthRoutes.CHALLENGE),
    EndpointRef("POST", routes.AuthRoutes.TOKEN_AUTH),
    EndpointRef("POST", routes.AuthRoutes.XADES_SIGNATURE),
    EndpointRef("GET", routes.AuthRoutes.AUTH_STATUS),
    EndpointRef("POST", routes.AuthRoutes.REDEEM_TOKEN),
    EndpointRef("POST", routes.AuthRoutes.REFRESH_TOKEN),
    EndpointRef("GET", routes.AuthRoutes.LIST_SESSIONS),
    EndpointRef("DELETE", routes.AuthRoutes.TERMINATE_CURRENT_SESSION),
    EndpointRef("DELETE", routes.AuthRoutes.TERMINATE_AUTH_SESSION),
]

__encryption_endpoints__ = [
    EndpointRef("GET", routes.EncryptionRoutes.PUBLIC_KEY_CERTIFICATES),
]

__invoices_endpoints__ = [
    EndpointRef("GET", routes.InvoiceRoutes.DOWNLOAD),
    EndpointRef("POST", routes.InvoiceRoutes.SEND),
]

__invoices_query_endpoints__ = [
    EndpointRef("POST", routes.InvoiceRoutes.QUERY_METADATA),
    EndpointRef("POST", routes.InvoiceRoutes.EXPORT),
    EndpointRef("GET", routes.InvoiceRoutes.EXPORT_STATUS),
]

__invoices_status_endpoints__ = [
    EndpointRef("GET", routes.SessionRoutes.LIST_SESSIONS),
    EndpointRef("GET", routes.InvoiceRoutes.SESSION_STATUS),
    EndpointRef("GET", routes.InvoiceRoutes.LIST_SESSION_INVOICES),
    EndpointRef("GET", routes.InvoiceRoutes.SESSION_INVOICE_STATUS),
    EndpointRef("GET", routes.InvoiceRoutes.LIST_FAILED_SESSION_INVOICES),
    EndpointRef("GET", routes.InvoiceRoutes.INVOICE_UPO_BY_KSEF),
    EndpointRef("GET", routes.InvoiceRoutes.INVOICE_UPO_BY_REFERENCE),
]

__collective_identifier_endpoints__ = [
    EndpointRef("POST", routes.CollectiveIdentifierRoutes.GENERATE),
    EndpointRef("POST", routes.CollectiveIdentifierRoutes.QUERY),
    EndpointRef("GET", routes.CollectiveIdentifierRoutes.QUERY_BY_KSEF_NUMBER),
    EndpointRef("GET", routes.CollectiveIdentifierRoutes.LIST_INVOICES),
]

__session_endpoints__ = [
    EndpointRef("POST", routes.SessionRoutes.OPEN_ONLINE),
    EndpointRef("POST", routes.SessionRoutes.TERMINATE_ONLINE),
    EndpointRef("GET", routes.SessionRoutes.GET_SESSION_UPO),
    EndpointRef("POST", routes.SessionRoutes.OPEN_BATCH),
    EndpointRef("POST", routes.SessionRoutes.CLOSE_BATCH),
]

__testdata_endpoints__ = [
    EndpointRef("POST", routes.TestDataRoutes.CREATE_SUBJECT),
    EndpointRef("POST", routes.TestDataRoutes.DELETE_SUBJECT),
    EndpointRef("POST", routes.TestDataRoutes.CREATE_PERSON),
    EndpointRef("POST", routes.TestDataRoutes.DELETE_PERSON),
    EndpointRef("POST", routes.TestDataRoutes.GRANT_PERMISSIONS),
    EndpointRef("POST", routes.TestDataRoutes.REVOKE_PERMISSIONS),
    EndpointRef("POST", routes.TestDataRoutes.ENABLE_ATTACHMENTS),
    EndpointRef("POST", routes.TestDataRoutes.REVOKE_ATTACHMENTS),
    EndpointRef("POST", routes.TestDataRoutes.BLOCK_CONTEXT),
    EndpointRef("POST", routes.TestDataRoutes.UNBLOCK_CONTEXT),
    EndpointRef("PUT", routes.TestDataRoutes.UPDATE_CERTIFICATE),
]

__tokens_endpoints__ = [
    EndpointRef("POST", routes.TokenRoutes.GENERATE_TOKEN),
    EndpointRef("GET", routes.TokenRoutes.LIST_TOKENS),
    EndpointRef("GET", routes.TokenRoutes.TOKEN_STATUS),
    EndpointRef("DELETE", routes.TokenRoutes.REVOKE_TOKEN),
]

__permissions_endpoints__ = [
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_PERSON),
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_ENTITY),
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_AUTHORIZATION),
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_INDIRECT),
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_SUBUNITS),
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_EU_ENTITY),
    EndpointRef("POST", routes.GrantPermissionsRoutes.GRANT_ADMINISTERED_EU_ENTITY),
    EndpointRef(
        "DELETE",
        routes.RevokePermissionsRoutes.REVOKE_AUTHORIZATION_PERMISSION,
    ),
    EndpointRef("DELETE", routes.RevokePermissionsRoutes.REVOKE_PERMISSION),
    EndpointRef("GET", routes.QueryPermissionsRoutes.QUERY_ATTACHMENTS_STATUS),
    EndpointRef(
        "GET",
        routes.QueryPermissionsRoutes.QUERY_OPERATIONS_STATUS,
    ),
    EndpointRef("GET", routes.QueryPermissionsRoutes.QUERY_ENTITY_ROLES),
    EndpointRef("POST", routes.QueryPermissionsRoutes.QUERY_AUTHORIZATIONS_GRANTS),
    EndpointRef("POST", routes.QueryPermissionsRoutes.QUERY_EU_ENTITIES_GRANTS),
    EndpointRef("POST", routes.QueryPermissionsRoutes.QUERY_PERSONAL_GRANTS),
    EndpointRef("POST", routes.QueryPermissionsRoutes.QUERY_PERSONS_GRANTS),
    EndpointRef("POST", routes.QueryPermissionsRoutes.QUERY_SUBORDINATE_ENTITIES_ROLES),
    EndpointRef("POST", routes.QueryPermissionsRoutes.QUERY_SUBUNITS_GRANTS),
]

__limits_endpoints__ = [
    EndpointRef("GET", routes.LimitRoutes.GET_CONTEXT_LIMITS),
    EndpointRef("GET", routes.LimitRoutes.GET_SUBJECT_LIMITS),
    EndpointRef("GET", routes.LimitRoutes.GET_API_RATE_LIMITS),
    EndpointRef("POST", routes.LimitRoutes.SET_SESSION_LIMITS),
    EndpointRef("DELETE", routes.LimitRoutes.RESET_SESSION_LIMITS),
    EndpointRef("POST", routes.LimitRoutes.SET_SUBJECT_LIMITS),
    EndpointRef("DELETE", routes.LimitRoutes.RESET_SUBJECT_LIMITS),
    EndpointRef("POST", routes.LimitRoutes.SET_API_RATE_LIMITS),
    EndpointRef("DELETE", routes.LimitRoutes.RESET_API_RATE_LIMITS),
    EndpointRef("POST", routes.LimitRoutes.SET_PRODUCTION_RATE_LIMITS),
]

__certificates_endpoints__ = [
    EndpointRef("GET", routes.CertificateRoutes.LIMITS),
    EndpointRef("GET", routes.CertificateRoutes.ENROLLMENT_DATA),
    EndpointRef("POST", routes.CertificateRoutes.ENROLLMENT),
    EndpointRef("GET", routes.CertificateRoutes.ENROLLMENT_STATUS),
    EndpointRef("POST", routes.CertificateRoutes.RETRIEVE),
    EndpointRef("POST", routes.CertificateRoutes.REVOKE),
    EndpointRef("POST", routes.CertificateRoutes.QUERY),
]

__peppol_endpoints__ = [
    EndpointRef("GET", routes.PeppolRoutes.QUERY_PROVIDERS),
]

__all_endpoints__: list[EndpointRef] = [
    *__auth_endpoints__,
    *__certificates_endpoints__,
    *__encryption_endpoints__,
    *__invoices_endpoints__,
    *__invoices_query_endpoints__,
    *__invoices_status_endpoints__,
    *__collective_identifier_endpoints__,
    *__peppol_endpoints__,
    *__session_endpoints__,
    *__testdata_endpoints__,
    *__tokens_endpoints__,
    *__permissions_endpoints__,
    *__limits_endpoints__,
]
