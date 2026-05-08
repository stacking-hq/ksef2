from typing import Literal

from ksef2.infra.schema.api.supp.base import BaseSupp
from ksef2.infra.schema.api.spec.models import FormCode


class EncryptionInfo(BaseSupp):
    encryptedSymmetricKey: str
    """
    Klucz symetryczny o długości 32 bajtów, zaszyfrowany algorytmem RSA (Padding: OAEP z SHA-256), zakodowany w formacie Base64.

    [Klucz publiczny Ministerstwa Finansów](/docs/v2/index.html#tag/Certyfikaty-klucza-publicznego)
    """
    initializationVector: str
    """
    Wektor inicjalizujący (IV) o długości 16 bajtów, używany do szyfrowania symetrycznego, zakodowany w formacie Base64.
    """
    publicKeyId: str | None = None
    """
    Identyfikator klucza publicznego użytego do szyfrowania.
    """


class OpenOnlineSessionRequest(BaseSupp):
    formCode: FormCode
    """
    Schemat faktur wysyłanych w ramach sesji.

    Obsługiwane schematy:
    | SystemCode | SchemaVersion | Value |
    | --- | --- | --- |
    | [FA (2)](https://github.com/CIRFMF/ksef-docs/blob/main/faktury/schemy/FA/schemat_FA(2)_v1-0E.xsd) | 1-0E | FA |
    | [FA (3)](https://github.com/CIRFMF/ksef-docs/blob/main/faktury/schemy/FA/schemat_FA(3)_v1-0E.xsd) | 1-0E | FA |
    | [PEF (3)](https://github.com/CIRFMF/ksef-docs/blob/main/faktury/schemy/PEF/Schemat_PEF(3)_v2-1.xsd) | 2-1 | PEF |
    | [PEF_KOR (3)](https://github.com/CIRFMF/ksef-docs/blob/main/faktury/schemy/PEF/Schemat_PEF_KOR(3)_v2-1.xsd) | 2-1 | PEF |

    """
    encryption: EncryptionInfo
    """
    Symetryczny klucz szyfrujący pliki XML, zaszyfrowany kluczem publicznym Ministerstwa Finansów.
    """


ListSessionsQueryParams = Literal[
    "sessionType",
    "referenceNumber",
    "dateCreatedFrom",
    "dateCreatedTo",
    "dateClosedFrom",
    "dateClosedTo",
    "dateModifiedFrom",
    "dateModifiedTo",
    "statuses",
]


class ListSessionsParams(BaseSupp):
    pageSize: int | None = None
    sessionType: Literal["Online", "Batch"]
    referenceNumber: str | None = None
    dateCreatedFrom: str | None = None
    dateCreatedTo: str | None = None
    dateClosedFrom: str | None = None
    dateClosedTo: str | None = None
    dateModifiedFrom: str | None = None
    dateModifiedTo: str | None = None
    statuses: list[Literal["InProgress", "Succeeded", "Failed", "Cancelled"]] | None = (
        None
    )
