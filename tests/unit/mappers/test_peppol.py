from datetime import datetime, timezone

from polyfactory import BaseFactory

from ksef2._domain.models import peppol
from ksef2._infra.mappers.peppol import from_spec
from ksef2._infra.schema.api import spec


class TestPeppolMapper:
    def test_map_peppol_provider(self):
        mapped_input = spec.PeppolProvider(
            id="PPL123456",
            name="Test Provider",
            dateCreated=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, peppol.PeppolProvider)
        assert output.id == mapped_input.id
        assert output.name == mapped_input.name
        assert output.date_created == mapped_input.dateCreated

    def test_map_peppol_provider_with_null_name(self):
        mapped_input = spec.PeppolProvider(
            id="PPL123456",
            name=None,
            dateCreated=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, peppol.PeppolProvider)
        assert output.id == mapped_input.id
        assert output.name is None

    def test_map_query_peppol_providers_response(
        self, peppol_providers_resp: BaseFactory[spec.QueryPeppolProvidersResponse]
    ):
        mapped_input = peppol_providers_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, peppol.ListPeppolProvidersResponse)
        assert len(output.providers) == len(mapped_input.peppolProviders)
        assert output.has_more == mapped_input.hasMore

    def test_map_query_peppol_providers_response_empty_list(
        self, peppol_providers_resp: BaseFactory[spec.QueryPeppolProvidersResponse]
    ):
        mapped_input = peppol_providers_resp.build(peppolProviders=[], hasMore=False)
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, peppol.ListPeppolProvidersResponse)
        assert len(output.providers) == 0
        assert output.has_more is False
