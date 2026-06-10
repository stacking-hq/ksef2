from enum import StrEnum


class GrantPermissionsRoutes(StrEnum):
    GRANT_PERSON = "/permissions/persons/grants"
    GRANT_ENTITY = "/permissions/entities/grants"
    GRANT_AUTHORIZATION = "/permissions/authorizations/grants"
    GRANT_INDIRECT = "/permissions/indirect/grants"
    GRANT_SUBUNITS = "/permissions/subunits/grants"
    GRANT_ADMINISTERED_EU_ENTITY = "/permissions/eu-entities/administration/grants"
    GRANT_EU_ENTITY = "/permissions/eu-entities/grants"


class RevokePermissionsRoutes(StrEnum):
    REVOKE_PERMISSION = "/permissions/common/grants/{permissionId}"
    REVOKE_AUTHORIZATION_PERMISSION = (
        "/permissions/authorizations/grants/{permissionId}"
    )


class QueryPermissionsRoutes(StrEnum):
    QUERY_ENTITIES_GRANTS = "/permissions/query/entities/grants"
    QUERY_PERSONAL_GRANTS = "/permissions/query/personal/grants"
    QUERY_ATTACHMENTS_STATUS = "/permissions/attachments/status"
    QUERY_OPERATIONS_STATUS = "/permissions/operations/{referenceNumber}"
    QUERY_ENTITY_ROLES = "/permissions/query/entities/roles"
    QUERY_AUTHORIZATIONS_GRANTS = "/permissions/query/authorizations/grants"
    QUERY_EU_ENTITIES_GRANTS = "/permissions/query/eu-entities/grants"
    QUERY_PERSONS_GRANTS = "/permissions/query/persons/grants"
    QUERY_SUBORDINATE_ENTITIES_ROLES = "/permissions/query/subordinate-entities/roles"
    QUERY_SUBUNITS_GRANTS = "/permissions/query/subunits/grants"


class PeppolRoutes(StrEnum):
    QUERY_PROVIDERS = "/peppol/query"


class TestDataRoutes(StrEnum):
    __test__ = False

    CREATE_SUBJECT = "/testdata/subject"
    DELETE_SUBJECT = "/testdata/subject/remove"
    CREATE_PERSON = "/testdata/person"
    DELETE_PERSON = "/testdata/person/remove"
    GRANT_PERMISSIONS = "/testdata/permissions"
    REVOKE_PERMISSIONS = "/testdata/permissions/revoke"
    ENABLE_ATTACHMENTS = "/testdata/attachment"
    REVOKE_ATTACHMENTS = "/testdata/attachment/revoke"
    BLOCK_CONTEXT = "/testdata/context/block"
    UNBLOCK_CONTEXT = "/testdata/context/unblock"


class LimitRoutes(StrEnum):
    GET_CONTEXT_LIMITS = "/limits/context"
    GET_SUBJECT_LIMITS = "/limits/subject"
    GET_API_RATE_LIMITS = "/rate-limits"
    SET_SESSION_LIMITS = "/testdata/limits/context/session"
    RESET_SESSION_LIMITS = "/testdata/limits/context/session"
    SET_SUBJECT_LIMITS = "/testdata/limits/subject/certificate"
    RESET_SUBJECT_LIMITS = "/testdata/limits/subject/certificate"
    SET_API_RATE_LIMITS = "/testdata/rate-limits"
    RESET_API_RATE_LIMITS = "/testdata/rate-limits"
    SET_PRODUCTION_RATE_LIMITS = "/testdata/rate-limits/production"


class TokenRoutes(StrEnum):
    GENERATE_TOKEN = "/tokens"
    LIST_TOKENS = "/tokens"
    TOKEN_STATUS = "/tokens/{referenceNumber}"
    REVOKE_TOKEN = "/tokens/{referenceNumber}"


class AuthRoutes(StrEnum):
    CHALLENGE = "/auth/challenge"
    TOKEN_AUTH = "/auth/ksef-token"
    XADES_SIGNATURE = "/auth/xades-signature"
    AUTH_STATUS = "/auth/{referenceNumber}"
    REDEEM_TOKEN = "/auth/token/redeem"
    REFRESH_TOKEN = "/auth/token/refresh"
    LIST_SESSIONS = "/auth/sessions"
    TERMINATE_CURRENT_SESSION = "/auth/sessions/current"
    TERMINATE_AUTH_SESSION = "/auth/sessions/{referenceNumber}"


class EncryptionRoutes(StrEnum):
    PUBLIC_KEY_CERTIFICATES = "/security/public-key-certificates"


class SessionRoutes(StrEnum):
    OPEN_ONLINE = "/sessions/online"
    TERMINATE_ONLINE = "/sessions/online/{referenceNumber}/close"
    OPEN_BATCH = "/sessions/batch"
    CLOSE_BATCH = "/sessions/batch/{referenceNumber}/close"
    GET_SESSION_UPO = "/sessions/{referenceNumber}/upo/{upoReferenceNumber}"
    LIST_SESSIONS = "/sessions"


class InvoiceRoutes(StrEnum):
    QUERY_METADATA = "/invoices/query/metadata"
    EXPORT = "/invoices/exports"
    EXPORT_STATUS = "/invoices/exports/{referenceNumber}"
    DOWNLOAD = "/invoices/ksef/{ksefNumber}"
    SEND = "/sessions/online/{referenceNumber}/invoices"
    SESSION_STATUS = "/sessions/{referenceNumber}"
    LIST_SESSION_INVOICES = "/sessions/{referenceNumber}/invoices"
    SESSION_INVOICE_STATUS = (
        "/sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}"
    )
    LIST_FAILED_SESSION_INVOICES = "/sessions/{referenceNumber}/invoices/failed"
    INVOICE_UPO_BY_KSEF = "/sessions/{referenceNumber}/invoices/ksef/{ksefNumber}/upo"
    INVOICE_UPO_BY_REFERENCE = (
        "/sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}/upo"
    )


class CertificateRoutes(StrEnum):
    LIMITS = "/certificates/limits"
    ENROLLMENT_DATA = "/certificates/enrollments/data"
    ENROLLMENT = "/certificates/enrollments"
    ENROLLMENT_STATUS = "/certificates/enrollments/{referenceNumber}"
    RETRIEVE = "/certificates/retrieve"
    REVOKE = "/certificates/{certificateSerialNumber}/revoke"
    QUERY = "/certificates/query"


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
]

RETRYABLE_POST_PATHS = frozenset(
    {
        AuthRoutes.CHALLENGE,
        AuthRoutes.REDEEM_TOKEN,
        AuthRoutes.REFRESH_TOKEN,
        InvoiceRoutes.QUERY_METADATA,
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
