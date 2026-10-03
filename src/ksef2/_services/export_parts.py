from pathlib import Path


def safe_part_filename(part_name: str) -> str:
    """Return a sanitized local filename for an export package part.

    Raises:
        ValueError: If ``part_name`` is unsafe or cannot produce a local filename.
    """
    sanitized_part_name = Path(part_name.replace("\\", "/")).name
    output_filename = sanitized_part_name.removesuffix(".aes")
    if (
        "\x00" in output_filename
        or output_filename.startswith(".")
        or output_filename in {"", ".", ".."}
    ):
        raise ValueError(f"Invalid export package part name: {part_name!r}")
    return output_filename
