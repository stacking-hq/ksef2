---
title: Mapa operacji API
description: Znajdź moduł raw i grupę metod ksef2 dla wybranego obszaru KSeF.
---

Grupy operacji niskiego poziomu są cienkimi fasadami nad metodami SDK odpowiadającymi operacjom API. Są dostępne przez `client.raw` przed uwierzytelnieniem i `auth.raw` po uwierzytelnieniu.

## Przed uwierzytelnieniem

| Moduł | Metody |
| --- | --- |
| `client.raw.auth` | `challenge`, `token_auth`, `xades_auth`, `auth_status`, `auth_status_rev2`, `redeem_token`, `refresh_token` |
| `client.raw.encryption` | `fetch_public_certificates` |
| `client.raw.peppol` | `query_providers` |
| `client.raw.testdata` | `create_subject`, `delete_subject`, `create_person`, `delete_person`, `grant_permissions`, `revoke_permissions`, `enable_attachments`, `revoke_attachments`, `block_context`, `unblock_context` |

`client.raw.testdata` jest dostępne tylko w `Environment.TEST`.

## Po uwierzytelnieniu

| Moduł | Metody |
| --- | --- |
| `auth.raw.auth` | `list_sessions`, `list_sessions_rev2`, `terminate_current_session`, `terminate_auth_session`; także metody auth, gdy są związane z uwierzytelnionym transportem |
| `auth.raw.certificates` | `get_limits`, `get_enrollment_data`, `enroll`, `get_enrollment_status`, `retrieve`, `revoke`, `query` |
| `auth.raw.collective_identifiers` | `generate`, `query`, `query_by_ksef_number`, `list_invoices` |
| `auth.raw.encryption` | `fetch_public_certificates` |
| `auth.raw.invoices` | `query_metadata`, `export`, `get_export_status`, `download`, `send`, `get_session_status`, `list_session_invoices`, `list_failed_session_invoices`, `get_session_invoice_status`, `get_invoice_upo_by_ksef`, `get_invoice_upo_by_reference` |
| `auth.raw.limits` | `get_context_limits`, `get_subject_limits`, `get_api_rate_limits`, `set_session_limits`, `reset_session_limits`, `set_subject_limits`, `reset_subject_limits`, `set_api_rate_limits`, `reset_api_rate_limits`, `set_production_rate_limits` |
| `auth.raw.peppol` | `query_providers` |
| `auth.raw.permissions.grant` | `grant_person`, `grant_entity`, `grant_authorization`, `grant_indirect`, `grant_subunit`, `grant_administered_eu_entity`, `grant_eu_entity` |
| `auth.raw.permissions.revoke` | `revoke_person`, `revoke_authorization` |
| `auth.raw.permissions.query` | `query_entities_grants`, `query_personal_grants`, `query_attachments_status`, `query_authorizations_grants`, `query_eu_entities_grants`, `query_persons_grants`, `query_subordinate_entities_roles`, `query_subunits_grants` |
| `auth.raw.permissions.status` | `query_operation_status`, `query_entity_roles` |
| `auth.raw.session` | `open_online`, `terminate_online`, `open_batch`, `close_batch`, `get_session_upo`, `list_sessions` |
| `auth.raw.testdata` | Te same metody co `client.raw.testdata` oraz `expire_token_approval`. |
| `auth.raw.tokens` | `generate_token`, `generate_token_rev2`, `list_tokens`, `list_tokens_rev2`, `token_status`, `token_status_rev2`, `approve_token`, `revoke_token` |

Użyj `spec.GenerateTokenRequestRev2` w `generate_token_rev2()`, aby podać opcjonalne daty ważności. Token utworzony w sesji uwierzytelnionej tokenem wymaga zatwierdzenia w odpowiednio uprawnionej sesji uwierzytelnionej podpisem XAdES lub przez Węzeł Krajowy. Przed użyciem tokena sprawdź jego zatwierdzenie i ważność metodą `token_status_rev2()`.

## Importy

```python
from ksef2.raw import (
    encrypt_invoice,
    encrypt_symmetric_key,
    encrypt_token,
    generate_session_key,
    prepare_batch_package,
    sha256_b64,
    spec,
    supp,
)
from ksef2.raw.mappers import auth as auth_mapper
```

Używaj `spec` i `supp` dla wspieranych modeli zgodnych ze schematem. Nie importuj wygenerowanych modeli z prywatnego pakietu schematów SDK w kodzie aplikacji.
