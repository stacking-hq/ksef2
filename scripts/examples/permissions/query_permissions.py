"""Query several permission views in the TEST environment.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- creating permission data to query
- querying people, authorizations, entities, and subunits
"""

import time
from dataclasses import dataclass

from ksef2 import Client, Environment
from ksef2.models import (
    AuthorizationPermissionsQuery,
    EuEntityPermissionsQuery,
    EntityPermission,
    Identifier,
    OffsetPaginationParams,
    Permission,
    PersonalPermissionsQuery,
    PersonPermissionsQuery,
    SubordinateEntityRolesQuery,
    SubunitPermissionsQuery,
)
from scripts.examples._common import generate_example_nip, generate_example_pesel


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        organization_nip = generate_example_nip()
        partner_nip = generate_example_nip()
        person_nip = generate_example_nip()
        person_pesel = generate_example_pesel()

        with client.testdata.temporal() as temp:
            temp.create_subject(
                nip=organization_nip,
                subject_type="enforcement_authority",
                description="SDK test org",
            )
            temp.create_subject(
                nip=partner_nip,
                subject_type="enforcement_authority",
                description="SDK test partner",
            )
            temp.create_person(
                nip=person_nip,
                pesel=person_pesel,
                description="Example person",
            )
            temp.grant_permissions(
                permissions=[
                    Permission(
                        type="credentials_manage",
                        description="Manage credentials",
                    ),
                    Permission(
                        type="invoice_read",
                        description="Read invoices",
                    ),
                ],
                grant_to=Identifier(type="nip", value=person_nip),
                in_context_of=Identifier(type="nip", value=organization_nip),
            )

            auth = client.authentication.with_test_certificate(nip=organization_nip)

            _ = auth.permissions.grant_entity(
                subject_value=partner_nip,
                permissions=[
                    EntityPermission(type="invoice_read", can_delegate=False),
                ],
                description="Partner invoice read access",
                entity_name="Test Partner Entity",
            )
            _ = auth.permissions.grant_authorization(
                subject_type="nip",
                subject_value=partner_nip,
                permission="self_invoicing",
                description="Self-invoicing authorization",
                entity_name="Test Partner Entity",
            )
            _ = auth.permissions.grant_person(
                subject_type="pesel",
                subject_value=person_pesel,
                permissions=["invoice_read", "invoice_write"],
                description="Person invoice access",
                first_name="John",
                last_name="Doe",
            )

            time.sleep(5)

            print("Get all persons permissions...")
            resp = auth.permissions.query_persons(
                query=PersonPermissionsQuery(
                    query_type="in_context",
                ),
            )
            print(resp.model_dump_json(indent=2))

            print("Get persons permissions with credentials manage permission...")
            resp = auth.permissions.query_persons(
                query=PersonPermissionsQuery(
                    query_type="in_context",
                    permission_types=["credentials_manage"],
                ),
            )
            print(resp.model_dump_json(indent=2))

            print("Query granted authorizations...")
            resp = auth.permissions.query_authorizations(
                query=AuthorizationPermissionsQuery(
                    query_type="granted",
                ),
            )
            print(resp.model_dump_json(indent=2))

            print("Query received authorizations...")
            resp = auth.permissions.query_personal(
                query=PersonalPermissionsQuery(),
            )
            print(resp.model_dump_json(indent=2))

            print("Query active personal permissions...")
            resp = auth.permissions.query_personal(
                query=PersonalPermissionsQuery(
                    permission_state="active",
                ),
            )
            print(resp.model_dump_json(indent=2))

            print("Query EU entities...")
            resp = auth.permissions.query_eu_entities(
                query=EuEntityPermissionsQuery(),
            )
            print(resp.model_dump_json(indent=2))

            print("Query subordinate entities...")
            resp = auth.permissions.query_subordinate_entities(
                query=SubordinateEntityRolesQuery(),
            )
            print(resp.model_dump_json(indent=2))

            print("Query subunits...")
            resp = auth.permissions.query_subunits(
                query=SubunitPermissionsQuery(),
            )
            print(resp.model_dump_json(indent=2))

            print("Query authorizations (received, page_size=20)...")
            resp = auth.permissions.query_authorizations(
                query=AuthorizationPermissionsQuery(
                    query_type="received",
                ),
                params=OffsetPaginationParams(page_offset=0, page_size=20),
            )
            print(resp.model_dump_json(indent=2))


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
