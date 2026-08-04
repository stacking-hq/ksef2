"""Grant person and entity permissions in the TEST environment.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- creating temporary subject and person data
- granting permissions to a person and an entity
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from ksef2.models import EntityPermission, Identifier, Permission
from scripts.examples._common import generate_example_nip, generate_example_pesel


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        organization_nip = generate_example_nip()
        person_nip = generate_example_nip()
        person_pesel = generate_example_pesel()

        with client.testdata.temporal() as temp:
            temp.create_subject(
                nip=organization_nip,
                subject_type="enforcement_authority",
                description="SDK test seller",
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
                ],
                grant_to=Identifier(type="nip", value=person_nip),
                in_context_of=Identifier(type="nip", value=organization_nip),
            )

            auth = client.authentication.with_test_certificate(nip=organization_nip)

            print("Granting person permissions...")
            result = auth.permissions.grant_person(
                subject_type="pesel",
                subject_value=person_pesel,
                permissions=["invoice_read", "invoice_write"],
                description="Test person permissions",
                first_name="John",
                last_name="Doe",
            )
            print(f"Person permissions granted: {result.reference_number}")

            print("Granting entity permissions...")
            result = auth.permissions.grant_entity(
                subject_value=organization_nip,
                permissions=[
                    EntityPermission(
                        type="invoice_read",
                        can_delegate=True,
                    ),
                ],
                description="Test entity permissions",
                entity_name="Test Entity",
            )
            print(f"Entity permissions granted: {result.reference_number}")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
