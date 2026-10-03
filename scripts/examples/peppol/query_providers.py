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
    client = Client(environment=config.environment)

    print("Fetching one page of PEPPOL providers...")
    page = client.peppol.list(
        params=OffsetPaginationParams(
            page_size=config.page_size,
            page_offset=config.page_offset,
        )
    ).first_page()
    for provider in page:
        print(provider.model_dump_json(indent=2))

    print("Iterating PEPPOL providers from the beginning...")
    for provider in client.peppol.list():
        print(provider.model_dump_json(indent=2))
        break

    print("Iterating PEPPOL providers with page offset ...")
    for provider in client.peppol.list(
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
