"""Integration tests for the Peppol service provider listing."""

import pytest

from ksef2 import Client
from ksef2._domain.models.pagination import OffsetPaginationParams


@pytest.mark.integration
class TestPeppolList:
    """Tests for ``client.peppol.list()``.

    The underlying endpoint is public and does not require authentication.
    """

    def test_list_peppol_providers_default_pagination(
        self, real_client: Client
    ) -> None:
        """Test listing Peppol providers with default pagination."""
        providers = real_client.peppol.list().first_page()

        assert isinstance(providers, list)

    def test_list_peppol_providers_custom_page_size(self, real_client: Client) -> None:
        """Test listing Peppol providers with custom page size."""
        providers = real_client.peppol.list(
            params=OffsetPaginationParams(page_size=20)
        ).first_page()

        # Should return at most 20 providers
        assert len(providers) <= 20

    def test_list_peppol_providers_pagination(self, real_client: Client) -> None:
        """Test paging through Peppol providers."""
        pages = real_client.peppol.list(
            params=OffsetPaginationParams(page_offset=0, page_size=10)
        ).pages()

        page1 = next(pages, [])
        page2 = next(pages, [])

        # Pages should be different (if both have results)
        if page1 and page2:
            assert page1[0].id != page2[0].id

    def test_peppol_provider_structure(self, real_client: Client) -> None:
        """Test that Peppol provider objects have expected fields."""
        providers = real_client.peppol.list().first_page()

        if providers:
            provider = providers[0]
            # Check required fields
            assert hasattr(provider, "id")
            assert hasattr(provider, "name")
            assert hasattr(provider, "date_created")

            # ID should match pattern P[A-Z]{2}[0-9]{6}
            assert provider.id.startswith("P")
            assert len(provider.id) == 9
