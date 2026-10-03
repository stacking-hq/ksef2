import pytest

from ksef2._services.export_parts import safe_part_filename


@pytest.mark.parametrize(
    ("part_name", "expected"),
    [
        ("part-1.zip.aes", "part-1.zip"),
        ("../unsafe/subdir/part-1.zip.aes", "part-1.zip"),
        ("..\\unsafe\\subdir\\part-2.zip.aes", "part-2.zip"),
        ("report.aes.backup.zip.aes", "report.aes.backup.zip"),
    ],
)
def test_safe_part_filename_returns_sanitized_filename(
    part_name: str,
    expected: str,
) -> None:
    assert safe_part_filename(part_name) == expected


@pytest.mark.parametrize(
    "part_name",
    ["", ".", "..", ".aes", ".hidden.zip.aes", "bad\x00.zip.aes"],
)
def test_safe_part_filename_rejects_invalid_names(part_name: str) -> None:
    with pytest.raises(ValueError, match="Invalid export package part name"):
        _ = safe_part_filename(part_name)
