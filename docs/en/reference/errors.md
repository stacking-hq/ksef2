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
text or nothing):

```text
KSeF rejected <METHOD> <path> (HTTP <status>, KSeF code <code>): <description>
Details: <detail>; <detail>
Trace ID: <trace id>
Hint: <hint>
```

The `KSeF code` part is left out when the response has no code, and the
`Details`, `Trace ID` and `Hint` lines appear only when there is something to
show. KSeF sends a trace ID with `application/problem+json` responses. The response body is not part of the message; it stays on `response`. When
the body is not a recognizable error, the description is a short, truncated
snippet of it.

For example, downloading an invoice UPO that KSeF has not issued yet (the
description and details are KSeF's own words, which are Polish):

```text
KSeF rejected GET /sessions/online/S1/invoices/I1/upo (HTTP 400, KSeF code 21178): Nie znaleziono UPO dla podanych kryteriów.
Details: UPO o numerze referencyjnym I1 nie zostało znalezione.
Hint: KSeF has not issued the UPO yet. Wait for processing to finish and request it again: `download_upo()` on a session or an invoice submission waits for processing first.
```

## Hints

`KSeFException.hint` says what to do next. It is shown on its own `Hint:` line in
`str(exc)` and stored in `exc.context["hint"]`. A hint is set only when the SDK
knows the cause, every method it names is a current one, and it can be replaced
for one occurrence by passing `hint=...` to the exception.

Hints on API errors come from one table, looked up by HTTP status and KSeF code:

| HTTP status | KSeF code | Class | Hint |
| --- | --- | --- | --- |
| any | 21165 | `KSeFNotReadyError` | KSeF has processed the invoice but has not made it available yet. Call `download()` with a `timeout` so the SDK keeps polling until it is. |
| any | 21178 | `KSeFNotReadyError` | KSeF has not issued the UPO yet. Wait for processing to finish and request it again: `download_upo()` on a session or an invoice submission waits for processing first. |
| 401 | any | `KSeFAuthError` | KSeF rejected the credentials or the access token. Authenticate again with `client.authentication.with_token()` or `client.authentication.with_xades()`, and check that the token or certificate is valid for this context. |
| 403 | any | `KSeFAuthError` | The authenticated identity is not allowed to do this in the current context. Check the reason in `details`, and grant the missing permission with the permissions client, for example `grant_person()`. |

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
are plain `KSeFApiError` with `ksef_code` set. The codes below come from the KSeF
API documentation.

| KSeF code | Meaning |
| --- | --- |
| `21001` | Unreadable content. |
| `21111` | Invalid authorization challenge. |
| `21115` | Invalid certificate. |
| `21117` | Invalid subject identifier for the context type. |
| `21155` | Number of invoices allowed in a session exceeded. |
| `21157` | Invalid package part size. |
| `21161` | Number of package parts exceeded. |
| `21164` | An invoice with the given identifier does not exist. |
| `21165` | The invoice with the given KSeF number is not available yet. `KSeFNotReadyError`. |
| `21166` | Technical correction unavailable. |
| `21167` | The invoice status does not allow a technical correction. |
| `21173` | No session with the given reference number. |
| `21175` | The query result with the given identifier does not exist. |
| `21178` | No UPO found for the given criteria. `KSeFNotReadyError`. |
| `21180` | The session status does not allow the operation. |
| `21181` | Invalid invoice export request. |
| `21182` | Limit of running exports reached. |
| `21183` | The filter range is outside the available data range. |
| `21184` | Session temporarily unavailable. |
| `21205` | The package cannot be empty. |
| `21208` | Timeout for upload or finish requests exceeded. |
| `21217` | Invalid character encoding. |
| `21301` | No authorization. |
| `21304` | No authentication. |
| `21308` | Attempt to use the authorization methods of a deceased person. |
| `21401` | The document does not match the XSD schema. |
| `21402` | Invalid file size. |
| `21403` | Invalid file hash. |
| `21405` | Input validation error. `ExceptionCode.VALIDATION_ERROR`. |
| `21406` | Signature and authentication type conflict. |
| `21418` | The continuation token is invalid. |
| `21470` | The key identifier is unknown or points to a retired key. |
| `25001` | Cannot fetch CSR data for the authentication method used. |
| `25002` | Cannot submit a certificate request with the authentication method used. |
| `25003` | The CSR data does not match the authentication vector. |
| `25004` | Invalid CSR format or signature. |
| `25005` | No certificate request with the given reference number. |
| `25006` | Limit of certificate requests reached. |
| `25007` | Limit of held certificates reached. |
| `25008` | No certificate with the given serial number. |
| `25009` | The certificate is already revoked, blocked or invalid. |
| `25010` | Invalid key type or length. |
| `25011` | Invalid CSR signature algorithm. |
| `26001` | A token cannot get permissions you do not hold. |
| `26002` | Cannot generate a token for the current context type. |
| `30001` | The entity or permission already exists. `ExceptionCode.OBJECT_ALREADY_EXISTS`. |
| `71001` | An invoice with the given identifier does not exist. |
| `71002` | The invoice is already assigned to the maximum number of collective identifiers. |
| `71004` | The invoices have different sellers. |
| `71005` | A KSeF number is repeated in the request. |

## ExceptionCode values

| Name | Value |
| --- | --- |
| `UNKNOWN_ERROR` | `10000` |
| `OBJECT_ALREADY_EXISTS` | `30001` |
| `VALIDATION_ERROR` | `21405` |
| `UPO_NOT_FOUND` | `21178` |
| `NOT_PROCESSED_YET` | `21165` |

Unknown numeric KSeF codes map to `ExceptionCode.UNKNOWN_ERROR`, but the raw
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
waits for KSeF to finish processing before it downloads, so it does not fail with
`KSeFNotReadyError` or a session error because it was called too early. It takes
`timeout` and `poll_interval` like `wait()` and raises the same timeout and
failure errors.

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
