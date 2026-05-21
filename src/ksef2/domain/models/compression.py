from enum import StrEnum
from typing import Literal

type CompressionType = Literal["zip", "tar_gz"]
type CompressionTypeSpecValue = Literal["Zip", "TarGz"]


class CompressionTypeEnum(StrEnum):
    ZIP = "Zip"
    TAR_GZ = "TarGz"


_COMPRESSION_TYPE_TO_SPEC: dict[CompressionType, CompressionTypeSpecValue] = {
    "zip": "Zip",
    "tar_gz": "TarGz",
}
_COMPRESSION_TYPE_FROM_SPEC: dict[CompressionTypeSpecValue, CompressionType] = {
    value: key for key, value in _COMPRESSION_TYPE_TO_SPEC.items()
}


def normalize_compression_type(
    value: CompressionType | CompressionTypeEnum | str,
) -> CompressionType:
    if isinstance(value, CompressionTypeEnum):
        return _COMPRESSION_TYPE_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _COMPRESSION_TYPE_TO_SPEC:
        return lowered_value  # pyright: ignore[reportReturnType]

    if value in _COMPRESSION_TYPE_FROM_SPEC:
        return _COMPRESSION_TYPE_FROM_SPEC[value]  # pyright: ignore[index]

    raise ValueError(
        f"Invalid compression type: {value}. Valid compression types are: "
        f"{', '.join(_COMPRESSION_TYPE_TO_SPEC)}"
    )


def compression_type_to_spec(
    value: CompressionType | CompressionTypeEnum | str,
) -> CompressionTypeSpecValue:
    return _COMPRESSION_TYPE_TO_SPEC[normalize_compression_type(value)]
