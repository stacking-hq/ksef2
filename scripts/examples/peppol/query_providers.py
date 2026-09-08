"""Query PEPPOL providers.

Prerequisites:
- none;

What it demonstrates:
- querying PEPPOL providers
- iterating over all PEPPOL providers automatically
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from ksef2.models import OffsetPaginationParams


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    page_size: int = 20
    page_offset: int = 10


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        print("Querying PEPPOL providers...")
        providers = client.peppol.query(
            params=OffsetPaginationParams(
                page_size=config.page_size,
                page_offset=config.page_offset,
            )
        )
        print(providers.model_dump_json(indent=2))

        print("Querying all PEPPOL from the beginning...")
        for provider in client.peppol.all():
            print(provider.model_dump_json(indent=2))
            break

        print("Querying all PEPPOL providers with page offset ...")
        for provider in client.peppol.all(
            params=OffsetPaginationParams(
                page_size=config.page_size,
                page_offset=config.page_offset,
            )
        ):
            print(provider.model_dump_json(indent=2))
            break


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
