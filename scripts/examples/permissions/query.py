"""Query attachment permission status in the TEST environment.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- authenticating in TEST
- querying attachment permission status
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from scripts.examples._common import generate_example_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        organization_nip = generate_example_nip()

        with client.testdata.temporal() as temp:
            temp.create_subject(
                nip=organization_nip,
                subject_type="enforcement_authority",
                description="Permission query example",
            )

            auth = client.authentication.with_test_certificate(nip=organization_nip)

            print(
                auth.permissions.get_attachment_permission_status().model_dump_json(
                    indent=2
                )
            )


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
