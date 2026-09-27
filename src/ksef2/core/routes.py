"""Route registry: each constant is a (method, path) pair and its path string."""

from enum import StrEnum


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class Route(StrEnum):
    """Path string that also carries the HTTP method it is called with.

    Members are `str`, so `path=routes.CollectiveIdentifierRoutes.QUERY` keeps
    working. The enum value is the `"METHOD /path"` key, which keeps the two
    methods of one path (for example `GET` and `POST /tokens`) as two distinct
    members instead of collapsing them into an alias.
    """

    method: HttpMethod
    path: str

    def __new__(cls, method: HttpMethod, path: str) -> "Route":
        obj = str.__new__(cls, path)
        obj._value_ = f"{method} {path}"
        obj.method = method
        obj.path = path
        return obj


class GrantPermissionsRoutes(Route):
    GRANT_PERSON = (HttpMethod.POST, "/permissions/persons/grants")
    GRANT_ENTITY = (HttpMethod.POST, "/permissions/entities/grants")
    GRANT_AUTHORIZATION = (HttpMethod.POST, "/permissions/authorizations/grants")
    GRANT_INDIRECT = (HttpMethod.POST, "/permissions/indirect/grants")
    GRANT_SUBUNITS = (HttpMethod.POST, "/permissions/subunits/grants")
    GRANT_ADMINISTERED_EU_ENTITY = (
        HttpMethod.POST,
        "/permissions/eu-entities/administration/grants",
    )
    GRANT_EU_ENTITY = (HttpMethod.POST, "/permissions/eu-entities/grants")


class RevokePermissionsRoutes(Route):
    REVOKE_PERMISSION = (HttpMethod.DELETE, "/permissions/common/grants/{permissionId}")
    REVOKE_AUTHORIZATION_PERMISSION = (
        HttpMethod.DELETE,
        "/permissions/authorizations/grants/{permissionId}",
    )


class QueryPermissionsRoutes(Route):
    QUERY_ENTITIES_GRANTS = (HttpMethod.POST, "/permissions/query/entities/grants")
    QUERY_PERSONAL_GRANTS = (HttpMethod.POST, "/permissions/query/personal/grants")
    QUERY_ATTACHMENTS_STATUS = (HttpMethod.GET, "/permissions/attachments/status")
    QUERY_OPERATIONS_STATUS = (
        HttpMethod.GET,
        "/permissions/operations/{referenceNumber}",
    )
    QUERY_ENTITY_ROLES = (HttpMethod.GET, "/permissions/query/entities/roles")
    QUERY_AUTHORIZATIONS_GRANTS = (
        HttpMethod.POST,
        "/permissions/query/authorizations/grants",
    )
    QUERY_EU_ENTITIES_GRANTS = (
        HttpMethod.POST,
        "/permissions/query/eu-entities/grants",
    )
    QUERY_PERSONS_GRANTS = (HttpMethod.POST, "/permissions/query/persons/grants")
    QUERY_SUBORDINATE_ENTITIES_ROLES = (
        HttpMethod.POST,
        "/permissions/query/subordinate-entities/roles",
    )
    QUERY_SUBUNITS_GRANTS = (HttpMethod.POST, "/permissions/query/subunits/grants")


class PeppolRoutes(Route):
    QUERY_PROVIDERS = (HttpMethod.GET, "/peppol/query")


class TestDataRoutes(Route):
    __test__ = False
    CREATE_SUBJECT = (HttpMethod.POST, "/testdata/subject")
    DELETE_SUBJECT = (HttpMethod.POST, "/testdata/subject/remove")
    CREATE_PERSON = (HttpMethod.POST, "/testdata/person")
    DELETE_PERSON = (HttpMethod.POST, "/testdata/person/remove")
    GRANT_PERMISSIONS = (HttpMethod.POST, "/testdata/permissions")
    REVOKE_PERMISSIONS = (HttpMethod.POST, "/testdata/permissions/revoke")
    ENABLE_ATTACHMENTS = (HttpMethod.POST, "/testdata/attachment")
    REVOKE_ATTACHMENTS = (HttpMethod.POST, "/testdata/attachment/revoke")
    BLOCK_CONTEXT = (HttpMethod.POST, "/testdata/context/block")
    UNBLOCK_CONTEXT = (HttpMethod.POST, "/testdata/context/unblock")
    UPDATE_CERTIFICATE = (HttpMethod.PUT, "/testdata/certificates/{serialNumber}")


class LimitRoutes(Route):
    GET_CONTEXT_LIMITS = (HttpMethod.GET, "/limits/context")
    GET_SUBJECT_LIMITS = (HttpMethod.GET, "/limits/subject")
    GET_API_RATE_LIMITS = (HttpMethod.GET, "/rate-limits")
    SET_SESSION_LIMITS = (HttpMethod.POST, "/testdata/limits/context/session")
    RESET_SESSION_LIMITS = (HttpMethod.DELETE, "/testdata/limits/context/session")
    SET_SUBJECT_LIMITS = (HttpMethod.POST, "/testdata/limits/subject/certificate")
    RESET_SUBJECT_LIMITS = (HttpMethod.DELETE, "/testdata/limits/subject/certificate")
    SET_API_RATE_LIMITS = (HttpMethod.POST, "/testdata/rate-limits")
    RESET_API_RATE_LIMITS = (HttpMethod.DELETE, "/testdata/rate-limits")
    SET_PRODUCTION_RATE_LIMITS = (HttpMethod.POST, "/testdata/rate-limits/production")


class TokenRoutes(Route):
    GENERATE_TOKEN = (HttpMethod.POST, "/tokens")
    LIST_TOKENS = (HttpMethod.GET, "/tokens")
    TOKEN_STATUS = (HttpMethod.GET, "/tokens/{referenceNumber}")
    REVOKE_TOKEN = (HttpMethod.DELETE, "/tokens/{referenceNumber}")


class AuthRoutes(Route):
    CHALLENGE = (HttpMethod.POST, "/auth/challenge")
    TOKEN_AUTH = (HttpMethod.POST, "/auth/ksef-token")
    XADES_SIGNATURE = (HttpMethod.POST, "/auth/xades-signature")
    AUTH_STATUS = (HttpMethod.GET, "/auth/{referenceNumber}")
    REDEEM_TOKEN = (HttpMethod.POST, "/auth/token/redeem")
    REFRESH_TOKEN = (HttpMethod.POST, "/auth/token/refresh")
    LIST_SESSIONS = (HttpMethod.GET, "/auth/sessions")
    TERMINATE_CURRENT_SESSION = (HttpMethod.DELETE, "/auth/sessions/current")
    TERMINATE_AUTH_SESSION = (HttpMethod.DELETE, "/auth/sessions/{referenceNumber}")


class EncryptionRoutes(Route):
    PUBLIC_KEY_CERTIFICATES = (HttpMethod.GET, "/security/public-key-certificates")


class SessionRoutes(Route):
    OPEN_ONLINE = (HttpMethod.POST, "/sessions/online")
    TERMINATE_ONLINE = (HttpMethod.POST, "/sessions/online/{referenceNumber}/close")
    OPEN_BATCH = (HttpMethod.POST, "/sessions/batch")
    CLOSE_BATCH = (HttpMethod.POST, "/sessions/batch/{referenceNumber}/close")
    GET_SESSION_UPO = (
        HttpMethod.GET,
        "/sessions/{referenceNumber}/upo/{upoReferenceNumber}",
    )
    LIST_SESSIONS = (HttpMethod.GET, "/sessions")


class InvoiceRoutes(Route):
    QUERY_METADATA = (HttpMethod.POST, "/invoices/query/metadata")
    EXPORT = (HttpMethod.POST, "/invoices/exports")
    EXPORT_STATUS = (HttpMethod.GET, "/invoices/exports/{referenceNumber}")
    DOWNLOAD = (HttpMethod.GET, "/invoices/ksef/{ksefNumber}")
    SEND = (HttpMethod.POST, "/sessions/online/{referenceNumber}/invoices")
    SESSION_STATUS = (HttpMethod.GET, "/sessions/{referenceNumber}")
    LIST_SESSION_INVOICES = (HttpMethod.GET, "/sessions/{referenceNumber}/invoices")
    SESSION_INVOICE_STATUS = (
        HttpMethod.GET,
        "/sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}",
    )
    LIST_FAILED_SESSION_INVOICES = (
        HttpMethod.GET,
        "/sessions/{referenceNumber}/invoices/failed",
    )
    INVOICE_UPO_BY_KSEF = (
        HttpMethod.GET,
        "/sessions/{referenceNumber}/invoices/ksef/{ksefNumber}/upo",
    )
    INVOICE_UPO_BY_REFERENCE = (
        HttpMethod.GET,
        "/sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}/upo",
    )


class CollectiveIdentifierRoutes(Route):
    GENERATE = (HttpMethod.POST, "/collective-identifiers")
    QUERY = (HttpMethod.POST, "/collective-identifiers/query")
    QUERY_BY_KSEF_NUMBER = (HttpMethod.GET, "/collective-identifiers/ksef/{ksefNumber}")
    LIST_INVOICES = (HttpMethod.POST, "/collective-identifiers/invoices")


class CertificateRoutes(Route):
    LIMITS = (HttpMethod.GET, "/certificates/limits")
    ENROLLMENT_DATA = (HttpMethod.GET, "/certificates/enrollments/data")
    ENROLLMENT = (HttpMethod.POST, "/certificates/enrollments")
    ENROLLMENT_STATUS = (HttpMethod.GET, "/certificates/enrollments/{referenceNumber}")
    RETRIEVE = (HttpMethod.POST, "/certificates/retrieve")
    REVOKE = (HttpMethod.POST, "/certificates/{certificateSerialNumber}/revoke")
    QUERY = (HttpMethod.POST, "/certificates/query")


ALL_ROUTES = [
    *GrantPermissionsRoutes,
    *RevokePermissionsRoutes,
    *QueryPermissionsRoutes,
    *PeppolRoutes,
    *TestDataRoutes,
    *LimitRoutes,
    *TokenRoutes,
    *AuthRoutes,
    *EncryptionRoutes,
    *CertificateRoutes,
    *SessionRoutes,
    *InvoiceRoutes,
    *CollectiveIdentifierRoutes,
]

RETRYABLE_POST_PATHS = frozenset(
    {
        AuthRoutes.CHALLENGE,
        AuthRoutes.REFRESH_TOKEN,
        InvoiceRoutes.QUERY_METADATA,
        CollectiveIdentifierRoutes.QUERY,
        CollectiveIdentifierRoutes.LIST_INVOICES,
        CertificateRoutes.QUERY,
        CertificateRoutes.RETRIEVE,
        QueryPermissionsRoutes.QUERY_PERSONAL_GRANTS,
        QueryPermissionsRoutes.QUERY_AUTHORIZATIONS_GRANTS,
        QueryPermissionsRoutes.QUERY_EU_ENTITIES_GRANTS,
        QueryPermissionsRoutes.QUERY_PERSONS_GRANTS,
        QueryPermissionsRoutes.QUERY_SUBORDINATE_ENTITIES_ROLES,
        QueryPermissionsRoutes.QUERY_SUBUNITS_GRANTS,
    }
)
