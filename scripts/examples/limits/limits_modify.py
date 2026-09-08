"""Modify and reset API limits on TEST.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- modifying and resetting session limits
- modifying and resetting subject limits
- modifying and resetting API rate limits
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
                description="Limits modify test",
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

            print("Modifying session limits...")
            limits = auth.limits.get_context_limits()
            original_max = limits.online_session.max_invoices
            limits.online_session.max_invoices = 5000
            auth.limits.set_session_limits(limits=limits)
            print(f"  max_invoices: {original_max} -> 5000")

            print("  Resetting session limits...")
            auth.limits.reset_session_limits()

            print("Modifying subject limits...")
            subject_limits = auth.limits.get_subject_limits()
            if subject_limits.certificate:
                subject_limits.certificate.max_certificates = 10
                auth.limits.set_subject_limits(limits=subject_limits)
                print("  max_certificates -> 10")

            print("  Resetting subject limits...")
            auth.limits.reset_subject_limits()

            print("Modifying API rate limits...")
            rate_limits = auth.limits.get_api_rate_limits()
            rate_limits.invoice_send.per_second = 50
            rate_limits.invoice_send.per_minute = 200
            auth.limits.set_api_rate_limits(limits=rate_limits)
            print("  invoice_send: 50/request, 200/m")

            print("  Resetting API rate limits...")
            auth.limits.reset_api_rate_limits()

            print("\nSetting production rate limits...")
            auth.limits.set_production_rate_limits()
            print("  Rate limits set to production values")

            prod_limits = auth.limits.get_api_rate_limits()
            inv = prod_limits.invoice_send
            print(
                f"  invoice_send: {inv.per_second}/request, {inv.per_minute}/m, {inv.per_hour}/h"
            )

            print("  Resetting to test defaults...")
            auth.limits.reset_api_rate_limits()

            print("All limits reset to defaults.")

        print("Test data cleaned up.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
