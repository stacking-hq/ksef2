from pathlib import Path

from scripts.validate_docs_paths import (
    CANONICAL_PROFILE_PATH,
    LEGACY_FALLBACK_PROFILE_PATH,
    OBSOLETE_PROFILE_PATH,
    validate_docs_paths,
)


def write_page(root: Path, relative: str, body: str) -> None:
    page = root / relative
    page.parent.mkdir(parents=True, exist_ok=True)
    _ = page.write_text(body, encoding="utf-8")


def test_validate_docs_paths_accepts_the_canonical_profile_path(
    tmp_path: Path,
) -> None:
    write_page(
        tmp_path,
        "en/how-to-guides/profiles.mdx",
        f"Profiles are stored in `{CANONICAL_PROFILE_PATH}`.\n",
    )

    assert validate_docs_paths(tmp_path) == []


def test_validate_docs_paths_reports_the_retired_profile_path(tmp_path: Path) -> None:
    write_page(
        tmp_path,
        "en/how-to-guides/legacy-profiles.mdx",
        f"New profiles are stored in `{OBSOLETE_PROFILE_PATH}`.\n"
        f"Legacy `{LEGACY_FALLBACK_PROFILE_PATH}` files are still readable.\n",
    )
    write_page(
        tmp_path,
        "pl/how-to-guides/profiles.mdx",
        f"Profil zapisujemy w `{CANONICAL_PROFILE_PATH}`.\n",
    )

    errors = validate_docs_paths(tmp_path)

    assert (
        f"en/how-to-guides/legacy-profiles.mdx: uses retired {OBSOLETE_PROFILE_PATH}"
        in errors
    )


def test_validate_docs_paths_reports_a_fallback_without_the_canonical_path(
    tmp_path: Path,
) -> None:
    write_page(
        tmp_path,
        "pl/how-to-guides/profiles.mdx",
        f"Starsze pliki `{LEGACY_FALLBACK_PROFILE_PATH}` nadal są odczytywane.\n",
    )

    errors = validate_docs_paths(tmp_path)

    assert (
        f"pl/how-to-guides/profiles.mdx: documents {LEGACY_FALLBACK_PROFILE_PATH} "
        f"without {CANONICAL_PROFILE_PATH}"
    ) in errors
    assert f"{tmp_path}: no page documents {CANONICAL_PROFILE_PATH}" in errors


def test_validate_docs_paths_fails_when_no_documentation_matches(
    tmp_path: Path,
) -> None:
    _ = (tmp_path / "diagram.svg").write_text("<svg/>", encoding="utf-8")

    errors = validate_docs_paths(tmp_path)

    assert errors == [f"{tmp_path}: no documentation files found to validate"]
