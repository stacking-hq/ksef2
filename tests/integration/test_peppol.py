"""Integration tests for Peppol service provider query endpoint."""

import pytest

from ksef2 import Client
from ksef2._domain.models.pagination import OffsetPaginationParams


@pytest.mark.integration
class TestPeppolQuery:
    """Tests for GET /peppol/query endpoint.

    This endpoint is public and does not require authentication.
    """

    def test_query_peppol_providers_default_pagination(
        self, real_client: Client
    ) -> None:
        """Test querying Peppol providers with default pagination."""
        response = real_client.peppol.query()

        # Response should have the expected structure
        assert hasattr(response, "providers")
        assert hasattr(response, "has_more")
        assert isinstance(response.providers, list)
        assert isinstance(response.has_more, bool)

    def test_query_peppol_providers_custom_page_size(self, real_client: Client) -> None:
        """Test querying Peppol providers with custom page size."""
        response = real_client.peppol.query(params=OffsetPaginationParams(page_size=20))

        assert isinstance(response.providers, list)
        # Should return at most 20 providers
        assert len(response.providers) <= 20

    def test_query_peppol_providers_pagination(self, real_client: Client) -> None:
        """Test pagination through Peppol providers."""
        # Get first page
        page1 = real_client.peppol.query(
            params=OffsetPaginationParams(page_offset=0, page_size=10)
        )

        # If there'request more, get second page
        if page1.has_more:
            page2 = real_client.peppol.query(
                params=OffsetPaginationParams(page_offset=1, page_size=10)
            )
            assert isinstance(page2.providers, list)

            # Pages should be different (if both have results)
            if page1.providers and page2.providers:
                assert page1.providers[0].id != page2.providers[0].id

    def test_peppol_provider_structure(self, real_client: Client) -> None:
        """Test that Peppol provider objects have expected fields."""
        response = real_client.peppol.query()

        if response.providers:
            provider = response.providers[0]
            # Check required fields
            assert hasattr(provider, "id")
            assert hasattr(provider, "name")
            assert hasattr(provider, "date_created")

            # ID should match pattern P[A-Z]{2}[0-9]{6}
            assert provider.id.startswith("P")
            assert len(provider.id) == 9
