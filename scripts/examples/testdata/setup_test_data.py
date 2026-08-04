"""Create TEST data with both automatic and manual cleanup flows.

Prerequisites:
- none; the script provisions all data it needs

What it demonstrates:
- using `temporal()` for automatic cleanup
- manually creating and deleting TEST data
"""

from dataclasses import dataclass

from ksef2 import Client, Environment, KSeFApiError
from ksef2.models import Identifier, Permission
from scripts.examples._common import generate_example_nip, generate_example_pesel


def with_automatic_cleanup(client: Client) -> None:
    """Set up test data with automatic cleanup."""
    organization_nip = generate_example_nip()
    person_nip = generate_example_nip()
    person_pesel = generate_example_pesel()

    print("Creating test data with automatic cleanup:")

    with client.testdata.temporal() as temp:
        print("Creating test subject...")
        temp.create_subject(
            nip=organization_nip,
            subject_type="enforcement_authority",
            description="Example organization",
        )

        print("Creating test person...")
        temp.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Example person",
        )

        try:
            temp.create_person(
                nip=person_nip,
                pesel=person_pesel,
                description="Example person",
            )
        except KSeFApiError:
            print("Person already exists: cleanup will still run on exit.")

        print("Granting permissions...")
        temp.grant_permissions(
            permissions=[
                Permission(type="invoice_read", description="Read invoices"),
                Permission(type="invoice_write", description="Send invoices"),
            ],
            grant_to=Identifier(type="nip", value=person_nip),
            in_context_of=Identifier(type="nip", value=organization_nip),
        )

    print("Cleanup has been performed automatically.")


def manual_cleanup(client: Client) -> None:
    """Manually set up and clean up test data."""
    organization_nip = generate_example_nip()
    person_nip = generate_example_nip()
    person_pesel = generate_example_pesel()

    print("Creating test data with manual cleanup:")

    print("Creating test subject...")
    client.testdata.create_subject(
        nip=organization_nip,
        subject_type="enforcement_authority",
        description="Example organization",
    )

    print("Creating test person...")
    client.testdata.create_person(
        nip=person_nip,
        pesel=person_pesel,
        description="Example person",
    )

    print("Trying to create already existing person...")
    try:
        client.testdata.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Example person",
        )
    except KSeFApiError:
        print("Person already exists: ...")

    print("Granting permissions...")
    client.testdata.grant_permissions(
        permissions=[
            Permission(type="invoice_read", description="Read invoices"),
            Permission(type="invoice_write", description="Send invoices"),
        ],
        grant_to=Identifier(type="nip", value=person_nip),
        in_context_of=Identifier(type="nip", value=organization_nip),
    )

    print("Cleaning up...")
    print("Revoking permissions...")
    client.testdata.revoke_permissions(
        revoke_from=Identifier(type="nip", value=person_nip),
        in_context_of=Identifier(type="nip", value=organization_nip),
    )

    print("Deleting test person...")
    client.testdata.delete_person(nip=person_nip)

    print("Deleting test subject...")
    client.testdata.delete_subject(nip=organization_nip)


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        with_automatic_cleanup(client)
        print()
        manual_cleanup(client)


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
