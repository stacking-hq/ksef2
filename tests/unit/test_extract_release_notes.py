import pytest

from scripts.extract_release_notes import extract_release_notes


def test_extract_release_notes_returns_only_requested_version() -> None:
    changelog = """## v1.0.0 (2026-08-04)

### Feat

- stable release

## v0.18.1 (2026-06-22)

- previous release
"""

    assert extract_release_notes(changelog, tag="v1.0.0") == (
        "## v1.0.0 (2026-08-04)\n\n### Feat\n\n- stable release\n"
    )


def test_extract_release_notes_rejects_missing_tag() -> None:
    with pytest.raises(ValueError, match="no section for v1.0.0"):
        extract_release_notes("## v0.18.1 (2026-06-22)\n", tag="v1.0.0")
