from datetime import datetime, timezone

from ksef2._domain.models import peppol
from ksef2._infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture


class PeppolProviderFactory(ModelFactory[spec.PeppolProvider]):
    id: str = "PPL123456"
    name: str = "Test Peppol Provider"
    dateCreated: datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)


@register_fixture(name="peppol_providers_resp")
class QueryPeppolProvidersResponseFactory(
    ModelFactory[spec.QueryPeppolProvidersResponse]
):
    @classmethod
    def peppolProviders(cls) -> list[spec.PeppolProvider]:
        return [PeppolProviderFactory.build()]


@register_fixture(name="domain_peppol_provider")
class DomainPeppolProviderFactory(ModelFactory[peppol.PeppolProvider]): ...


@register_fixture(name="domain_peppol_providers_list")
class DomainListPeppolProvidersResponseFactory(
    ModelFactory[peppol.ListPeppolProvidersResponse]
): ...
