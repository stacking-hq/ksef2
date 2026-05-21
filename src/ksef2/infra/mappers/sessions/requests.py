import base64
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.compression import compression_type_to_spec
from ksef2.domain.models.batch import (
    BatchFileInfo,
    BatchFilePart,
    OpenBatchSessionRequest,
)
from ksef2.domain.models.session import FormSchema, OpenOnlineSessionRequest
from ksef2.infra.schema.api import spec


@overload
def to_spec(request: OpenOnlineSessionRequest) -> spec.OpenOnlineSessionRequest: ...


@overload
def to_spec(request: OpenBatchSessionRequest) -> spec.OpenBatchSessionRequest: ...


@overload
def to_spec(request: FormSchema) -> spec.FormCode: ...


@overload
def to_spec(request: BatchFilePart) -> spec.BatchFilePartInfo: ...


@overload
def to_spec(request: BatchFileInfo) -> spec.BatchFileInfo: ...


def to_spec(request: BaseModel | FormSchema) -> object:
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel | FormSchema) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: FormSchema) -> spec.FormCode:
    return spec.FormCode(
        value=request.schema_value,
        systemCode=request.system_code,
        schemaVersion=request.schema_version,
    )


@_to_spec.register
def _(request: OpenOnlineSessionRequest) -> spec.OpenOnlineSessionRequest:
    return spec.OpenOnlineSessionRequest(
        formCode=to_spec(request.form_code),
        encryption=spec.EncryptionInfo(
            encryptedSymmetricKey=base64.b64encode(request.encrypted_key).decode(),
            initializationVector=base64.b64encode(request.iv).decode(),
            publicKeyId=request.public_key_id,
        ),
    )


@_to_spec.register
def _(request: BatchFilePart) -> spec.BatchFilePartInfo:
    return spec.BatchFilePartInfo(
        ordinalNumber=request.ordinal_number,
        fileSize=request.file_size,
        fileHash=request.file_hash,
    )


@_to_spec.register
def _(request: BatchFileInfo) -> spec.BatchFileInfo:
    return spec.BatchFileInfo(
        fileSize=request.file_size,
        fileHash=request.file_hash,
        compressionType=(
            spec.CompressionType(compression_type_to_spec(request.compression_type))
            if request.compression_type is not None
            else None
        ),
        fileParts=[to_spec(part) for part in request.parts],
    )


@_to_spec.register
def _(request: OpenBatchSessionRequest) -> spec.OpenBatchSessionRequest:
    return spec.OpenBatchSessionRequest(
        formCode=to_spec(request.form_code),
        batchFile=to_spec(request.batch_file),
        encryption=spec.EncryptionInfo(
            encryptedSymmetricKey=base64.b64encode(request.encrypted_key).decode(),
            initializationVector=base64.b64encode(request.iv).decode(),
            publicKeyId=request.public_key_id,
        ),
        offlineMode=request.offline_mode,
    )
