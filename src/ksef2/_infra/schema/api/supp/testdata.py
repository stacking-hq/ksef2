from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, Field, AwareDatetime


class SubUnit(BaseModel):
    subjectNip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]
    description: Annotated[
        str, Field(min_length=5, max_length=256, description="Opis podmiotu")
    ]


class CreateSubjectRequest(BaseModel):
    subjectNip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]
    subjectType: Annotated[
        Literal["EnforcementAuthority", "VatGroup", "JST"],
        Field(description="Typ podmiotu."),
    ]
    subunits: Annotated[
        list[SubUnit] | None,
        Field(default=None, description="Lista podrzędnych podmiotów"),
    ]
    description: Annotated[
        str, Field(min_length=5, max_length=256, description="Opis podmiotu")
    ]
    createdDate: Annotated[
        AwareDatetime | None,
        Field(default=None, description="Data utworzenia podmiotu"),
    ]


class DeleteSubjectRequest(BaseModel):
    subjectNip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]


class IdentifierInput(BaseModel):
    type: Annotated[
        Literal["Nip", "Pesel", "Fingerprint", "System"],
        Field(description="Typ identyfikatora"),
    ]
    value: Annotated[str, Field(description="Wartość identyfikatora")]


class PermissionInput(BaseModel):
    permissionType: Annotated[
        Literal[
            "InvoiceRead",
            "InvoiceWrite",
            "PefInvoiceWrite",
            "Introspection",
            "CredentialsRead",
            "CredentialsManage",
            "EnforcementOperations",
            "SubunitManage",
            "VatUeManage",
            "CollectiveIdentifierManage",
        ],
        Field(description="Typ uprawnienia"),
    ]
    description: Annotated[str, Field(description="Opis uprawnienia")]


class CreatePersonRequest(BaseModel):
    nip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]
    pesel: Annotated[
        str,
        Field(
            min_length=11,
            max_length=11,
            pattern=r"^\d{11}$",
            description="11 cyfrowy numer PESEL.",
        ),
    ]
    description: Annotated[
        str, Field(min_length=1, max_length=256, description="Opis osoby")
    ]
    isBailiff: Annotated[
        bool, Field(default=False, description="Czy osoba jest komornikiem")
    ]
    isDeceased: Annotated[bool, Field(default=False, description="Czy osoba nie żyje")]
    createdDate: Annotated[
        AwareDatetime | None,
        Field(default=None, description="Data utworzenia osoby"),
    ]


class DeletePersonRequest(BaseModel):
    nip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]


class GrantPermissionsRequest(BaseModel):
    contextIdentifier: Annotated[
        IdentifierInput, Field(description="Identyfikator kontekstu")
    ]
    authorizedIdentifier: Annotated[
        IdentifierInput, Field(description="Identyfikator upoważnionego")
    ]
    permissions: Annotated[
        list[PermissionInput],
        Field(description="Lista uprawnień"),
    ]


class RevokePermissionsRequest(BaseModel):
    contextIdentifier: Annotated[
        IdentifierInput, Field(description="Identyfikator kontekstu")
    ]
    authorizedIdentifier: Annotated[
        IdentifierInput, Field(description="Identyfikator upoważnionego")
    ]


class EnableAttachmentsRequest(BaseModel):
    nip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]


class RevokeAttachmentsRequest(BaseModel):
    nip: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$",
            description="10 cyfrowy numer NIP.",
        ),
    ]
    expectedEndDate: Annotated[
        date | None,
        Field(default=None, description="Oczekiwana data końcowa"),
    ]


class AuthContextIdentifierInput(BaseModel):
    type: Annotated[
        Literal["Nip", "InternalId", "NipVatUe", "PeppolId"],
        Field(description="Typ identyfikatora kontekstu"),
    ]
    value: Annotated[str, Field(description="Wartość identyfikatora")]


class BlockContextRequest(BaseModel):
    contextIdentifier: Annotated[
        AuthContextIdentifierInput,
        Field(description="Identyfikator kontekstu"),
    ]


class UnblockContextRequest(BaseModel):
    contextIdentifier: Annotated[
        AuthContextIdentifierInput,
        Field(description="Identyfikator kontekstu"),
    ]
