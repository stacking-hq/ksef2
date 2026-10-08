---
title: Error Reference
description: SDK exception hierarchy, attributes, KSeF error codes, hints, and polling timeout classes.
---

ksef2 raises SDK exceptions for failures it can classify. Transport failures
raised before KSeF returns a parsed API response remain `httpx.HTTPError`
exceptions. Presigned external-storage transfers use the dedicated exceptions
described below instead of KSeF API/authentication classification.

## Branch on the class or on `ksef_code`

Handle errors by exception class, or by `ksef_code` for KSeF API errors. Never
branch on the message text: messages are written for people, carry the current
KSeF wording and can change between releases. The same goes for `hint`: show it,
log it, but do not parse it.

## Base classes

| Class | Base | `code` | Main attributes |
| --- | --- | --- | --- |
| `KSeFException` | `Exception` | `SDK_ERROR` | `context`, `hint` |
| `KSeFApiError` | `KSeFException` | `API_ERROR` | `status_code`, `ksef_code`, `exception_code`, `trace_id`, `details`, `response` |
| `KSeFNotReadyError` | `KSeFApiError` | `NOT_READY` | API error attributes |
| `KSeFAuthError` | `KSeFApiError` | `AUTH_ERROR` | API error attributes |
| `KSeFAuthenticationExpiredError` | `KSeFAuthError` | `AUTHENTICATION_EXPIRED` | API error attributes |
| `KSeFRateLimitError` | `KSeFApiError` | `RATE_LIMIT_ERROR` | `retry_after` and the API error attributes |
| `KSeFExternalTransferError` | `KSeFException` | `EXTERNAL_TRANSFER_ERROR` | `operation`, `host`, `reference_number`, `part_ordinal`, `status_code`, `outcome_ambiguous` |
| `KSeFBatchUploadError` | `KSeFExternalTransferError` | `BATCH_UPLOAD_ERROR` | External-transfer attributes plus `recovery_state()` |
| `KSeFInvoiceRejectedError` | `KSeFSessionError` | `INVOICE_REJECTED` | `invoice_reference_number`, `invoice_status_code`, `description`, `details`, `extensions`, `status` |

Catch narrower subclasses before `KSeFException` when the workflow has a
specific recovery action.

```python
try:
    result = auth.invoices.query_metadata(filters=filters)
except KSeFRateLimitError as exc:
    retry_after = exc.retry_after
except KSeFNotReadyError:
    ...  # KSeF has not finished yet; wait and ask again
except KSeFApiError as exc:
    if exc.ksef_code == 21405:
        details = exc.details
    trace_id = exc.trace_id  # quote it when contacting KSeF support
except KSeFException as exc:
    context = exc.context
except httpx.HTTPError as exc:
    transport_error = exc
```

## SDK exception classes

| Class | `code` | Raised for |
| --- | --- | --- |
| `KSeFClientClosedError` | `CLIENT_CLOSED` | Root client or session client used after close. |
| `KSeFUnsupportedEnvironmentError` | `UNSUPPORTED_ENVIRONMENT` | TEST-only branch or flow used outside `Environment.TEST`. |
| `KSeFValidationError` | `VALIDATION_ERROR` | Invalid SDK input, invalid response payload, invalid profile config, or invalid session/batch arguments. |
| `KSeFArgumentError` | `ARGUMENT_ERROR` | A call combined arguments the SDK does not allow, such as both or neither of `form_code` and `state`. Subclass of both `KSeFValidationError` and `TypeError`. |
| `KSeFInvoiceRenderingError` | `INVOICE_RENDERING_ERROR` | Optional XSLT/PDF rendering failures. |
| `KSeFEncryptionError` | `ENCRYPTION_ERROR` | Token, symmetric-key, invoice encryption, or decryption failure. |
| `KSeFSessionError` | `SESSION_ERROR` | Session-state violation, such as using a closed session. Base class of `KSeFInvoiceRejectedError`. |
| `KSeFInvoiceRejectedError` | `INVOICE_REJECTED` | KSeF finished processing an online-session invoice and rejected it (`InvoiceSubmission.wait()`). |
| `KSeFExportFailedError` | `EXPORT_FAILED` | KSeF finished an invoice export without a package: it failed, was cancelled by the system or expired (`ExportJob.wait()`). |
| `KSeFPermissionOperationFailedError` | `PERMISSION_OPERATION_FAILED` | KSeF finished a permission grant or revoke without applying it (`PermissionOperation.wait()`). |
| `KSeFCertificateEnrollmentFailedError` | `CERTIFICATE_ENROLLMENT_FAILED` | KSeF rejected, cancelled or failed a certificate enrollment (`CertificateEnrollment.wait()`). |
| `KSeFAuthTokenRedemptionError` | `AUTH_TOKEN_REDEMPTION_ERROR` | A one-shot authentication redemption lost its response and may have succeeded. |
| `KSeFExternalTransferError` | `EXTERNAL_TRANSFER_ERROR` | A presigned external-storage upload or download was rejected or lost its response. |
| `KSeFBatchUploadError` | `BATCH_UPLOAD_ERROR` | A batch-part upload failed while protected recovery state remains available. |
| `NoCertificateAvailableError` | `NO_CERTIFICATE_AVAILABLE` | No valid certificate exists for signing or encryption usage. |
| `KSeFMetadataPaginationError` | `METADATA_PAGINATION_ERROR` | Metadata pagination cannot continue safely. |

`KSeFAuthTokenRedemptionError.outcome_ambiguous` is always `True`. Do not retry
the redemption: KSeF may already have consumed the temporary authentication
token even though the response did not reach the caller.

## External transfer attributes and batch recovery

Presigned storage responses are not KSeF API responses. A storage `403`, for
example, raises `KSeFExternalTransferError`, not `KSeFAuthError`. Its message and
`context` contain only the sanitized host, operation, workflow reference, part
ordinal, status code, and ambiguity flag; the signed URL is not included.

| Attribute | Type | Meaning |
| --- | --- | --- |
| `operation` | `Literal["upload", "download"]` | External transfer that failed. |
| `host` | `str` | Storage hostname without path, query, or signature. |
| `reference_number` | `str` | Export or batch workflow reference. |
| `part_ordinal` | `int` | One-based package part ordinal. |
| `status_code` | `int | None` | Storage response status, or `None` when no response arrived. |
| `outcome_ambiguous` | `bool` | `True` when an upload may have reached storage despite a lost response. |

`KSeFBatchUploadError.recovery_state()` deliberately reveals the sensitive
`BatchSessionResumeState` required for recovery. It is excluded from the error
message and `context` because it contains encryption material and presigned
URLs. Store it only in protected credential storage, and do not blindly retry
an upload when `outcome_ambiguous` is `True`.

The original `httpx` failure remains available through `__cause__`. Avoid
logging the cause indiscriminately because raw HTTP diagnostics can include the
signed URL.

## API error attributes

`KSeFApiError` is raised for parsed KSeF 4xx and 5xx responses. Specialized
subclasses are used for authentication/authorization failures, rate limits and
resources KSeF has not made available yet.

| Attribute | Type | Meaning |
| --- | --- | --- |
| `status_code` | `int` | HTTP status returned by KSeF. |
| `ksef_code` | `int | None` | Raw KSeF error code, whatever its value. `None` when the response carried none. This is the source of truth. |
| `exception_code` | `ExceptionCode` | The same code as an enum when the SDK lists it; `UNKNOWN_ERROR` otherwise. Kept for compatibility. |
| `trace_id` | `str | None` | KSeF trace ID of the request, when KSeF returned one. |
| `details` | `list[str]` | Detail messages KSeF attached to the error; empty when none. |
| `hint` | `str | None` | What to do next, when the SDK knows the cause. |
| `response` | `BaseModel | None` | Parsed KSeF error payload when parsing succeeded. |

The same values are available in `context`: `status_code`, `ksef_code`,
`trace_id`, `details` and `hint` (when there is one).

Use `response.model_dump()` or `response.model_dump_json()` for structured
diagnostics when `response` is not `None`.

### Message format

Every KSeF API error is formatted the same way, whatever shape the response had
(`application/problem+json`, the older `exception` payload, another JSON body,
text or nothing). The SDK picks the parser from the response `Content-Type`:
`application/problem+json` is read as Problem Details, `application/json` as the
older payload (except a 401, which KSeF sends as Problem Details labelled
`application/json`), and anything else becomes a short snippet:

```text
KSeF rejected <METHOD> <path> (HTTP <status>, KSeF code <code>): <description>
Details: <detail>; <detail>
Trace ID: <trace id>
Hint: <hint>
```

The `KSeF code` part is left out when the response has no code, and the
`Details`, `Trace ID` and `Hint` lines appear only when there is something to
show. By default the SDK sends `X-Error-Format: problem-details` on every
request to the KSeF API (see [Error format](#error-format)), so KSeF returns its
400 and 429 errors as `application/problem+json`, and `trace_id` is set on every
API error KSeF returns in that format. (401, 403 and 410 are always Problem
Details.) The header is not sent to presigned storage URLs. The response body is
not part of the message; it stays on `response`. When the body is not a
recognizable error, the description is a short, truncated snippet of it.

### Error format

`TransportConfig.error_format` chooses the format the SDK asks KSeF for:

| Value | Header sent | 400 and 429 errors |
| --- | --- | --- |
| `"problem-details"` (default) | `X-Error-Format: problem-details` | `application/problem+json`: `trace_id` is set and `response` is `BadRequestProblemDetails` / `TooManyRequestsProblemDetails` |
| `"legacy"` | none | `application/json`: no `trace_id`, and `response` is `ExceptionResponse` / `TooManyRequestsResponse` |

401, 403 and 410 are always Problem Details. The SDK reads both formats the same
way, so `ksef_code`, `details`, the class and the hint do not change; only
`trace_id` and the type of `response` do. Use `"legacy"` only if your code reads
`response` and expects the older models:

```python
client = Client(Environment.PRODUCTION, transport_config=TransportConfig(error_format="legacy"))
```

A Problem Details body that does not match its model in the KSeF spec (or comes
with a status the spec has no model for, such as 500) is not parsed: the
description is a snippet of the body and `response` is `None`.

For example, downloading an invoice UPO that KSeF has not issued yet (the
description and details are KSeF's own words, which are Polish):

```text
KSeF rejected GET /sessions/online/S1/invoices/I1/upo (HTTP 400, KSeF code 21178): Nie znaleziono UPO dla podanych kryteriów.
Details: UPO o numerze referencyjnym I1 nie zostało znalezione.
Trace ID: 0b1f6a7c-4d2e-4a53-9a6e-3f2b9d1c8e11
Hint: KSeF has no UPO for this yet. Call `wait()` on the invoice submission or the session first, then call `download_upo()` again. If `wait()` raises `KSeFInvoiceRejectedError`, KSeF rejected the invoice and will never issue a UPO for it.
```

## Hints

`KSeFException.hint` says what to do next. It is shown on its own `Hint:` line in
`str(exc)` and stored in `exc.context["hint"]`. A hint is set only when the SDK
knows the cause, every method it names is a current one, and it can be replaced
for one occurrence by passing `hint=...` to the exception.

Hints on API errors come from the KSeF code first, then the HTTP status. A
code with its own hint keeps it on a 401 or 403 too, and the class still
follows the status there (`KSeFAuthError`):

| HTTP status | KSeF code | Class | Hint |
| --- | --- | --- | --- |
| any | 21155 | `KSeFApiError` | The session has reached its invoice limit. Close it with `close()` and send the remaining invoices in a new session from `online_session()`. |
| any | 21165 | `KSeFNotReadyError` | KSeF has processed the invoice but has not made it available yet. Call `download()` with a `timeout` so the SDK keeps polling until it is. |
| any | 21178 | `KSeFNotReadyError` | KSeF has no UPO for this yet. Call `wait()` on the invoice submission or the session first, then call `download_upo()` again. If `wait()` raises `KSeFInvoiceRejectedError`, KSeF rejected the invoice and will never issue a UPO for it. |
| any | 21180 | `KSeFApiError` | The session is already closed or KSeF is processing it, so it accepts no more invoices. Send further invoices in a new session from `online_session()` or `batch_session()`. |
| any | 21182 | `KSeFApiError` | KSeF limits how many exports can run at once. Wait for a running export to finish with `wait()`, then call `export()` again. |
| any | 21183 | `KSeFApiError` | The date range reaches outside the data KSeF keeps. Narrow the date range in the filters passed to `search()`. |
| any | 21184 | `KSeFApiError` | KSeF cannot accept invoices in this session at the moment. Retry later, or send the invoice in a new session from `online_session()`. |
| any | 21208 | `KSeFApiError` | KSeF cancelled the batch session because the parts were not uploaded or the session was not closed in time. Send the package again in a new session from `batch_session()`. |
| any | 21418 | `KSeFApiError` | Continuation tokens come from KSeF and are only valid as returned. Iterate the pager the SDK returns, or use its `pages()`, instead of building or reusing a token yourself. |
| any | 21470 | `KSeFApiError` | KSeF does not know the public key the request was encrypted with, or has retired it. The SDK keeps KSeF certificates for 24 hours; create a new client so it loads the current ones. |
| any | 25006 | `KSeFApiError` | KSeF allows only a limited number of certificate enrollments. `get_limits()` shows how many are still allowed. |
| any | 25007 | `KSeFApiError` | You hold the maximum number of KSeF certificates. Revoke one you no longer use with `revoke()`, and check `get_limits()` for the limit. |
| any | 26001 | `KSeFApiError` | A token can only get permissions the authenticated identity holds. Request fewer permissions in `generate()`. |
| any | 30001 | `KSeFApiError` | The subject or person already exists on KSeF TEST. Reuse it, or remove it first with `delete_subject()` or `delete_person()`. |
| 401 | other | `KSeFAuthError` | KSeF rejected the credentials or the access token. Authenticate again with `client.authentication.with_token()` or `client.authentication.with_xades()`, and check that the token or certificate is valid for this context. |
| 403 | other | `KSeFAuthError` | The authenticated identity is not allowed to do this in the current context. Check the reason in `details`, and grant the missing permission with the permissions client, for example `grant_person()`. |

`KSeFRateLimitError` builds its hint from `retry_after`, for example
`Wait 17 seconds before retrying.`

Hints on the other SDK errors:

| Class | Hint |
| --- | --- |
| `KSeFArgumentError` | Pass exactly one of the mutually exclusive arguments named in the message. |
| `KSeFAuthPollingTimeoutError` | KSeF has not finished authenticating yet. Authenticate again with a larger `timeout` in `client.authentication.with_xades()` or `client.authentication.with_token()`. |
| `KSeFAuthenticationExpiredError` | Authenticate again with `client.authentication.with_token()` or `client.authentication.with_xades()`, or restore tokens that are still valid with `client.authentication.resume()`. |
| `KSeFBatchSessionTimeoutError` | KSeF may still be processing the batch. Call `wait()` on the batch session again with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `batch_session(state=...)`. |
| `KSeFCertificateEnrollmentFailedError` | Read `description` and `details` for the reason, then submit a corrected request with `enroll()`. `get_limits()` shows how many enrollments and certificates are still allowed. |
| `KSeFCertificateEnrollmentTimeoutError` | KSeF may still issue the certificate. Call `wait()` on the enrollment again with a larger `timeout`, or check it with `get_enrollment_status()`. |
| `KSeFExportFailedError` | Read `description` and `details` for the reason, then start a new export with `export()`. |
| `KSeFExportTimeoutError` | The export may still finish. Call `wait()` on the export again with a larger `timeout`. After a restart, get the job back with `export(state=...)` using the state saved from `resume_state()`. |
| `KSeFInvoiceDownloadTimeoutError` | KSeF has not made the invoice available yet. Call `download()` again with a larger `timeout`. |
| `KSeFInvoiceProcessingTimeoutError` | KSeF may still accept the invoice. Keep waiting with `submission(reference_number).wait()` on the session, with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `online_session(state=...)`. |
| `KSeFInvoiceQueryTimeoutError` | No invoice matched before the deadline. Call `wait()` again with a larger `timeout`, or check the filters passed to `search()`. |
| `KSeFInvoiceRejectedError` | Read `description` and `details` for the reason, fix the invoice and send it again with `send_invoice()`. |
| `KSeFNotReadyError` | KSeF has not finished preparing this resource. Wait and request it again. |
| `KSeFOnlineSessionTimeoutError` | KSeF may still be processing the session. Call `wait()` on the session again with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `online_session(state=...)`. |
| `KSeFPermissionOperationFailedError` | Read `description` for the reason, fix the request and grant or revoke again. `get_operation_status()` shows the operation's final state. |
| `KSeFPermissionOperationTimeoutError` | The operation may still be applied. Call `wait()` on the operation again with a larger `timeout`, or check it with `get_operation_status()`. |
| `KSeFTokenStatusTimeoutError` | KSeF may still be activating the token. Call `wait()` on the token again with a larger `timeout`, or check it with `get_status()`. |

`KSeFSessionError` has no class-level hint. The SDK sets one where it knows the
cause: waiting on a session that is still open (close it first), and a session
that KSeF finished with a failure (read the failed invoices). A rejected
duplicate (`440`) gets its own hint on `KSeFInvoiceRejectedError`.

## KSeF error codes

`ksef_code` is the number KSeF sent. The SDK never drops a code it does not know.
Only `21165` and `21178` have a dedicated class (`KSeFNotReadyError`); the rest
are plain `KSeFApiError` with `ksef_code` set (`KSeFAuthError` on a 401 or 403).
The codes below are every code the KSeF API documentation (`openapi.json`)
lists, all of them on HTTP 400 responses, and each has an `ExceptionCode`
member. A unit test fails when a spec update adds a code that is not listed.

`21178` does not always mean "not issued yet": KSeF also returns it, for good,
for an invoice it rejected (for example a duplicate, status 440). Call `wait()`
first; if it raises `KSeFInvoiceRejectedError`, there is no UPO to download.

| KSeF code | `ExceptionCode` | Meaning |
| --- | --- | --- |
| `9101` | `INVALID_DOCUMENT` | Invalid document. |
| `9102` | `MISSING_SIGNATURE` | No signature. |
| `9103` | `TOO_MANY_SIGNATURES` | Number of allowed signatures exceeded. |
| `9105` | `INVALID_SIGNATURE` | Invalid signature. |
| `21001` | `UNREADABLE_CONTENT` | Unreadable content. |
| `21111` | `INVALID_AUTH_CHALLENGE` | Invalid authorization challenge. |
| `21115` | `INVALID_CERTIFICATE` | Invalid certificate. |
| `21117` | `INVALID_CONTEXT_IDENTIFIER` | Invalid subject identifier for the context type. |
| `21155` | `SESSION_INVOICE_LIMIT_EXCEEDED` | Number of invoices allowed in a session exceeded. |
| `21157` | `INVALID_PACKAGE_PART_SIZE` | Invalid package part size. |
| `21161` | `PACKAGE_PART_LIMIT_EXCEEDED` | Number of package parts exceeded. |
| `21164` | `INVOICE_NOT_FOUND` | An invoice with the given identifier does not exist. |
| `21165` | `NOT_PROCESSED_YET` | The invoice with the given KSeF number is not available yet. `KSeFNotReadyError`. |
| `21166` | `TECHNICAL_CORRECTION_UNAVAILABLE` | Technical correction unavailable. |
| `21167` | `TECHNICAL_CORRECTION_NOT_ALLOWED` | The invoice status does not allow a technical correction. |
| `21173` | `SESSION_NOT_FOUND` | No session with the given reference number. |
| `21175` | `QUERY_RESULT_NOT_FOUND` | The query result with the given identifier does not exist. |
| `21178` | `UPO_NOT_FOUND` | No UPO found for the given criteria. `KSeFNotReadyError`. |
| `21180` | `SESSION_STATUS_FORBIDS_OPERATION` | The session status does not allow the operation. |
| `21181` | `INVALID_EXPORT_REQUEST` | Invalid invoice export request. |
| `21182` | `EXPORT_LIMIT_REACHED` | Limit of running exports reached. |
| `21183` | `FILTER_RANGE_OUT_OF_BOUNDS` | The filter range is outside the available data range. |
| `21184` | `SESSION_TEMPORARILY_UNAVAILABLE` | Session temporarily unavailable. |
| `21205` | `EMPTY_PACKAGE` | The package cannot be empty. |
| `21208` | `UPLOAD_WINDOW_EXCEEDED` | Timeout for upload or finish requests exceeded. |
| `21217` | `INVALID_CHARACTER_ENCODING` | Invalid character encoding. |
| `21301` | `NO_AUTHORIZATION` | No authorization. |
| `21304` | `NO_AUTHENTICATION` | No authentication. |
| `21308` | `DECEASED_PERSON_AUTHENTICATION` | Attempt to use the authorization methods of a deceased person. |
| `21401` | `SCHEMA_VALIDATION_FAILED` | The document does not match the XSD schema. |
| `21402` | `INVALID_FILE_SIZE` | Invalid file size. |
| `21403` | `INVALID_FILE_HASH` | Invalid file hash. |
| `21405` | `VALIDATION_ERROR` | Input validation error. |
| `21406` | `SIGNATURE_AUTH_TYPE_CONFLICT` | Signature and authentication type conflict. |
| `21418` | `INVALID_CONTINUATION_TOKEN` | The continuation token is invalid. |
| `21470` | `UNKNOWN_KEY_ID` | The key identifier is unknown or points to a retired key. |
| `25001` | `CSR_DATA_UNAVAILABLE` | Cannot fetch CSR data for the authentication method used. |
| `25002` | `ENROLLMENT_NOT_ALLOWED` | Cannot submit a certificate request with the authentication method used. |
| `25003` | `CSR_DATA_MISMATCH` | The CSR data does not match the authentication vector. |
| `25004` | `INVALID_CSR` | Invalid CSR format or signature. |
| `25005` | `ENROLLMENT_NOT_FOUND` | No certificate request with the given reference number. |
| `25006` | `ENROLLMENT_LIMIT_REACHED` | Limit of certificate requests reached. |
| `25007` | `CERTIFICATE_LIMIT_REACHED` | Limit of held certificates reached. |
| `25008` | `CERTIFICATE_NOT_FOUND` | No certificate with the given serial number. |
| `25009` | `CERTIFICATE_NOT_REVOCABLE` | The certificate is already revoked, blocked or invalid. |
| `25010` | `INVALID_KEY` | Invalid key type or length. |
| `25011` | `INVALID_CSR_SIGNATURE_ALGORITHM` | Invalid CSR signature algorithm. |
| `26001` | `TOKEN_PERMISSIONS_NOT_HELD` | A token cannot get permissions you do not hold. |
| `26002` | `TOKEN_CONTEXT_NOT_ALLOWED` | Cannot generate a token for the current context type. |
| `30001` | `OBJECT_ALREADY_EXISTS` | The entity or permission already exists. |
| `71001` | `COLLECTIVE_INVOICE_NOT_FOUND` | An invoice with the given identifier does not exist. |
| `71002` | `COLLECTIVE_IDENTIFIER_LIMIT_REACHED` | The invoice is already assigned to the maximum number of collective identifiers. |
| `71004` | `DIFFERENT_SELLERS` | The invoices have different sellers. |
| `71005` | `DUPLICATE_KSEF_NUMBER` | A KSeF number is repeated in the request. |

## ExceptionCode values

`ExceptionCode` is an `IntEnum`: each member's value is its KSeF code, and the
names are in the table above. One more member is not a KSeF code:

| Name | Value |
| --- | --- |
| `UNKNOWN_ERROR` | `10000` |

Codes the enum does not list map to `ExceptionCode.UNKNOWN_ERROR`, but the raw
number stays on `ksef_code`. Prefer `ksef_code` in new code.

## Polling timeout classes

Polling timeout exceptions mean the local wait deadline expired. They do not by
themselves prove the remote KSeF workflow failed.

| Class | `code` | Identifier attributes |
| --- | --- | --- |
| `KSeFAuthPollingTimeoutError` | `AUTH_POLLING_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFTokenStatusTimeoutError` | `TOKEN_STATUS_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFInvoiceQueryTimeoutError` | `INVOICE_QUERY_TIMEOUT` | `timeout` |
| `KSeFInvoiceDownloadTimeoutError` | `INVOICE_DOWNLOAD_TIMEOUT` | `ksef_number`, `timeout` |
| `KSeFInvoiceProcessingTimeoutError` | `INVOICE_PROCESSING_TIMEOUT` | `invoice_reference_number`, `timeout` |
| `KSeFExportTimeoutError` | `EXPORT_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFPermissionOperationTimeoutError` | `PERMISSION_OPERATION_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFCertificateEnrollmentTimeoutError` | `CERTIFICATE_ENROLLMENT_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFBatchSessionTimeoutError` | `BATCH_SESSION_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFOnlineSessionTimeoutError` | `ONLINE_SESSION_TIMEOUT` | `reference_number`, `timeout` |

Store the relevant reference before polling so another process can resume the
status check. Every timeout error carries a `hint` that says how to keep waiting
or resume.

`download_upo()` on an invoice submission, an online session and a batch session
never waits and has no `timeout`. Call `wait()` on the submission or the session
first. Asked too early it raises `KSeFNotReadyError`, with a hint that names
`wait()`; a session that is still open raises `KSeFSessionError`.

## Rate limit attributes

| Attribute | Type | Meaning |
| --- | --- | --- |
| `retry_after` | `int | None` | Whole seconds from KSeF `Retry-After`, given as seconds or as an HTTP date; `None` when absent or unreadable. |
| `status_code` | `int` | Always `429`. |
| `response` | `BaseModel | None` | Parsed KSeF error payload when available. |
| `hint` | `str` | `Wait <retry_after> seconds before retrying.` |

## Invoice rejection attributes

`KSeFInvoiceRejectedError` subclasses `KSeFSessionError`, so existing handlers
still catch it. Catch `KSeFInvoiceRejectedError` before `KSeFSessionError` when
only a session-state violation should reopen or re-authenticate a session.

| Attribute | Type | Meaning |
| --- | --- | --- |
| `invoice_reference_number` | `str` | Reference number of the rejected invoice. |
| `invoice_status_code` | `int` | KSeF invoice status, for example `440` or `450`. Not an HTTP status. |
| `description` | `str` | KSeF status description. |
| `details` | `list[str]` | KSeF status details; empty when absent. |
| `extensions` | `dict[str, str | None]` | KSeF status extensions; empty when absent. |
| `status` | `SessionInvoiceStatusResponse` | The full status response. |

Unlike `KSeFApiError.status_code`, which is always an HTTP status,
`invoice_status_code` comes from the KSeF invoice status object.

For a duplicate (`440`), `extensions` carries `originalKsefNumber` and
`originalSessionReferenceNumber`. A caller recovering from a send whose
response was lost can pass `originalKsefNumber` to `download_invoice()` and
compare it against the submitted invoice. If it is the same invoice, treat the
rejection as already accepted.

## Related reference

- [Operations reference](operations.md): Review retry behavior, rate limits, workflow timeouts, and resumable state.
- [Client lifecycle](client-lifecycle.md): Review lifecycle errors and client close behavior.
- [Status and UPO](../concepts/status-and-upo.md): Understand status surfaces, UPO documents, and polling deadlines.
