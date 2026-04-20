# API Surface Ergonomics Review — Pre-1.0

Baseline: post async-client refactor, post typing cleanup (1146 → 953 warnings).

---

## Summary

The API is well-designed overall. The layering makes sense for the domain (KSeF has a multi-step auth + session model). But there are a handful of ergonomic issues worth fixing before 1.0, roughly ordered by impact.

---

## 1. No minimal "happy path" — the simplest invoice requires too many steps

To send one invoice, a user writes:

```python
with Client(Environment.TEST) as client:
    authed = client.authentication.with_test_certificate(nip="1234567890")
    with authed.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice_and_wait(invoice_xml=xml_bytes)
```

That's 4 objects deep (`Client` → `AuthClient` → `AuthenticatedClient` → `OnlineSessionClient`). The middle two are pure ceremony for the most common case. Consider a convenience method on `Client`:

```python
with Client(Environment.TEST) as client:
    result = client.send_invoice(nip="1234567890", invoice_xml=xml_bytes)
```

This would handle auth (via test cert), session open, send, wait, session close, and return the result. Power users still have the full layered API. Same pattern for `send_batch`.

---

## 2. `context_type: ContextIdentifierType = "nip"` is a raw string literal

The parameter accepts `"nip" | "onip" | "pesel" | "nop"` as bare strings. Before 1.0, promote it to an enum or at minimum a `Literal` type that's exported and documented. Raw string APIs age poorly — users typo them silently.

---

## 3. `AuthenticatedClient` is the wrong name for what it is

`AuthenticatedClient` is actually the main object users spend 95% of their time interacting with. The name describes *how it was created*, not *what it does*. Consider renaming to something like `KSeFClient` or `Session` — and making `AuthenticatedClient` a private implementation detail. Same applies to `AuthClient` → could be `.auth` property with a clearer type name.

---

## 4. Builder `to_xml()` returns `str` but `send_invoice()` expects `bytes`

```python
xml = builder.to_xml()                    # returns str
session.send_invoice(invoice_xml=xml)      # expects bytes
```

Users must remember `xml.encode("utf-8")` every time. Either `to_xml()` should return `bytes`, or `send_invoice` should accept `str | bytes` and encode internally. The latter is more forgiving and costs nothing.

---

## 5. The builder discovers errors late

`builder.build()` raises `ValueError` if header/seller/buyer/body are missing. But you only discover this at `.build()` time, not at the point of the mistake. A `validate()` method or earlier checks in the chain would help. The builder also silently accepts `builder.standard().build()` without adding any rows — this passes validation but produces an invalid invoice that KSeF rejects.

---

## 6. `InvoicesFilter` and `InvoiceMetadataParams` are not exported

Users need `InvoicesFilter` to query invoices, but it's nested inside `ksef2.domain.models.invoices`. The top-level `__init__.py` exports `FormSchema` and configs but none of the query/filter types that every user needs. Either re-export them or document the import paths clearly.

---

## 7. Error messages could be more actionable

`KSeFApiError` currently shows:

```
API_ERROR/400: Invalid request
Response: {"exception":{"exceptionCode":...}}
```

But the raw JSON response is not what a user needs. Consider parsing the most common error codes into a short human-readable summary, or at least extracting `exceptionDescriptionList` into a formatted string. The `ExceptionCode` enum has only 5 values, which doesn't cover what the API actually returns.

---

## 8. `online_session()` and `batch_session()` are on the wrong object

These are session lifecycle operations that feel like they belong on a `sessions` factory, not on the authenticated client directly. The `AuthenticatedClient` has 12+ `@cached_property` sub-clients already. It's becoming a god object. Not critical for 1.0, but worth noting.

---

## 9. `fetch_package` reaches into transport internals

```python
self._download_transport = (
    transport._next
    if isinstance(transport, BearerTokenMiddleware)
    else transport
)
```

`InvoicesService` reaches through the middleware chain to get the raw transport for downloads (because presigned URLs don't need auth headers). This works but is fragile. Consider exposing a clean "download without auth" method on the transport layer.

---

## 10. beartype import side effects

`import ksef2` triggers `beartype_this_package()` globally. This is a reasonable design choice for an SDK, but it should be documented prominently — users who compose this SDK into their own apps may be surprised by runtime type checking overhead. Consider making it opt-in via an environment variable for library-to-library usage.

---

## Recommended priority for 1.0

1. **Make `send_invoice` accept `str | bytes`** — trivial, removes a papercut every user hits
2. **Export the common domain types** (`InvoicesFilter`, `InvoiceMetadataParams`, `KsefInvoice`, etc.) from the top-level package
3. **Replace `ContextIdentifierType` raw strings** with a proper `Literal` or enum
4. **Add a `validate()` method to the builder** or move the required-field checks earlier

The rest can wait. The layered API is correct for the domain — it just needs some rough edges sanded down.
