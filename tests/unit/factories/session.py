from ksef2.domain.models import batch as domain_batch
from ksef2.domain.models import session as domain_session
from ksef2.domain.models.pagination import ListSessionsQuery
from ksef2.infra.schema.api import spec
from ksef2.infra.schema.api.supp.batch import OpenBatchSessionRequest
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from tests.unit.helpers import VALID_BASE64, VALID_PUBLIC_KEY_ID


@register_fixture(name="session_open_online_req")
class OpenOnlineSessionRequestFactory(ModelFactory[spec.OpenOnlineSessionRequest]): ...


@register_fixture(name="session_open_online_resp")
class OpenOnlineSessionResponseFactory(
    ModelFactory[spec.OpenOnlineSessionResponse]
): ...


@register_fixture(name="domain_session_open_online_req")
class DomainOpenOnlineSessionRequestFactory(
    ModelFactory[domain_session.OpenOnlineSessionRequest]
):
    public_key_id: str = VALID_PUBLIC_KEY_ID
    form_code: domain_session.FormSchema = domain_session.FormSchema.FA3


@register_fixture(name="domain_session_list_query")
class DomainListSessionsQueryFactory(ModelFactory[ListSessionsQuery]):
    session_type: domain_session.SessionType = "online"
    reference_number = None
    date_created_from = None
    date_created_to = None
    date_closed_from = None
    date_closed_to = None
    date_modified_from = None
    date_modified_to = None
    statuses = None


@register_fixture(name="domain_session_open_batch_req")
class DomainOpenBatchSessionRequestFactory(
    ModelFactory[domain_batch.OpenBatchSessionRequest]
):
    encrypted_key: bytes = b"secret-batch-key"
    iv: bytes = b"\x00" * 16
    public_key_id: str = VALID_PUBLIC_KEY_ID
    form_code: domain_session.FormSchema = domain_session.FormSchema.FA3
    offline_mode: bool = False


@register_fixture(name="domain_batch_file_part")
class DomainBatchFilePartFactory(ModelFactory[domain_batch.BatchFilePart]):
    ordinal_number: int = 1
    file_size: int = 1024
    file_hash: str = VALID_BASE64


@register_fixture(name="domain_batch_file_info")
class DomainBatchFileInfoFactory(ModelFactory[domain_batch.BatchFileInfo]):
    file_size: int = 1024
    file_hash: str = VALID_BASE64

    @classmethod
    def parts(cls) -> list[domain_batch.BatchFilePart]:
        return [DomainBatchFilePartFactory.build()]


@register_fixture(name="domain_part_upload_request")
class DomainPartUploadRequestFactory(ModelFactory[domain_batch.PartUploadRequest]):
    ordinal_number: int = 1
    method: str = "PUT"
    url: str = "https://example.com/upload/part-1"
    headers: dict[str, str | None] = {"x-ms-blob-type": "BlockBlob"}


@register_fixture(name="domain_online_session_state")
class DomainOnlineSessionStateFactory(ModelFactory[domain_session.OnlineSessionState]):
    reference_number: str = "20250625-SO-2C3E6C8000-B675CF5D68-07"
    aes_key: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    iv: str = "MDEyMzQ1Njc4OWFiY2RlZg=="
    access_token: str = "fake-access-token"
    form_code: domain_session.FormSchema = domain_session.FormSchema.FA3


@register_fixture(name="domain_batch_session_state")
class DomainBatchSessionStateFactory(ModelFactory[domain_batch.BatchSessionState]):
    reference_number: str = "20250625-BS-2C3E6C8000-B675CF5D68-07"
    aes_key: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    iv: str = "MDEyMzQ1Njc4OWFiY2RlZg=="
    access_token: str = "fake-access-token"
    form_code: domain_session.FormSchema = domain_session.FormSchema.FA3

    @classmethod
    def part_upload_requests(cls) -> list[domain_batch.PartUploadRequest]:
        return [DomainPartUploadRequestFactory.build()]


@register_fixture(name="session_open_batch_req")
class OpenBatchSessionRequestFactory(ModelFactory[OpenBatchSessionRequest]): ...


@register_fixture(name="session_open_batch_resp")
class OpenBatchSessionResponseFactory(ModelFactory[spec.OpenBatchSessionResponse]): ...


@register_fixture(name="session_part_upload_req")
class PartUploadRequestFactory(ModelFactory[spec.PartUploadRequest]):
    ordinalNumber: int = 1
    method: str = "PUT"
    url: str = "https://example.com/upload/part-1"
    headers: dict[str, str | None] = {"x-ms-blob-type": "BlockBlob"}


@register_fixture(name="session_list_resp")
class SessionsQueryResponseFactory(ModelFactory[spec.SessionsQueryResponse]): ...
