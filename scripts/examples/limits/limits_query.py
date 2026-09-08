"""Query API limits using an authenticated client.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- querying context limits
- querying subject limits
- querying API rate limits
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from ksef2.models import Identifier, Permission
from scripts.examples._common import generate_example_nip, generate_example_pesel


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        organization_nip = generate_example_nip()
        person_nip = generate_example_nip()
        person_pesel = generate_example_pesel()

        print("Setting up test data...")
        with client.testdata.temporal() as temp:
            temp.create_subject(
                nip=organization_nip,
                subject_type="enforcement_authority",
                description="Limits query test",
            )

            temp.create_person(
                nip=person_nip,
                pesel=person_pesel,
                description="Example person",
            )

            temp.grant_permissions(
                permissions=[
                    Permission(type="invoice_write", description="Sending invoices"),
                ],
                grant_to=Identifier(type="nip", value=person_nip),
                in_context_of=Identifier(type="nip", value=organization_nip),
            )

            print("Authenticating...")
            auth = client.authentication.with_test_certificate(nip=organization_nip)

            print("Context limits (session type):")
            context_limits = auth.limits.get_context_limits()

            print("  Online session:")
            print(f"    Max invoices: {context_limits.online_session.max_invoices}")
            print(
                f"    Max invoice size (MB): "
                f"{context_limits.online_session.max_invoice_size_mb}"
            )
            print(
                f"    Max with attachment (MB): "
                f"{context_limits.online_session.max_invoice_with_attachment_size_mb}"
            )

            print("  Batch session:")
            print(f"    Max invoices: {context_limits.batch_session.max_invoices}")
            print(
                f"    Max invoice size (MB): "
                f"{context_limits.batch_session.max_invoice_size_mb}"
            )

            print("  Collective identifier:")
            print(
                f"    Max invoices: {context_limits.collective_identifier.max_invoices}"
            )

            print("Subject limits (certificate/enrollment):")
            subject_limits = auth.limits.get_subject_limits()
            if subject_limits.certificate:
                print(
                    f"  Max certificates: {subject_limits.certificate.max_certificates}"
                )
            if subject_limits.enrollment:
                print(
                    f"  Max enrollments:  {subject_limits.enrollment.max_enrollments}"
                )
            print("API rate limits:")
            rate_limits = auth.limits.get_api_rate_limits()
            inv = rate_limits.invoice_send
            print(
                f"  Invoice send: {inv.per_second}/s  {inv.per_minute}/m  {inv.per_hour}/h"
            )
            sess = rate_limits.online_session
            print(
                f"  Online session: {sess.per_second}/s  {sess.per_minute}/m  {sess.per_hour}/h"
            )
            dl = rate_limits.invoice_download
            print(
                f"  Invoice download: {dl.per_second}/s  {dl.per_minute}/m  {dl.per_hour}/h"
            )

            print("All limits queried successfully.")

        print("Test data cleaned up.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
