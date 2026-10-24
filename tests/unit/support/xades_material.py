"""Real XAdES material shared by the credential and authentication tests.

Everything here is generated, self-signed TEST-only material. It lives in one place
so a test that needs credentials in PEM, DER or PKCS#12 asks for the same bytes the
credential model was specified against.
"""

import datetime
from typing import Literal

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, ed25519, rsa
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    pkcs12,
)
from cryptography.x509 import Certificate
from cryptography.x509.oid import NameOID

from ksef2._domain.models.xades import XAdESCredentials

CredentialFormat = Literal["pem", "der", "pkcs12"]
TestKey = (
    rsa.RSAPrivateKey
    | ec.EllipticCurvePrivateKey
    | dsa.DSAPrivateKey
    | ed25519.Ed25519PrivateKey
)


def self_signed(key: TestKey, common_name: str = "ksef2 test") -> Certificate:
    """Return a self-signed certificate issued for the public half of *key*."""
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.UTC)
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(hours=1))
        .not_valid_after(now + datetime.timedelta(days=1))
    )
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return builder.sign(key, None)
    return builder.sign(key, hashes.SHA256())


def key_pem(key: TestKey, *, password: bytes | None = None) -> bytes:
    """Return *key* as PKCS#8 PEM, encrypted when a *password* is given."""
    return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, _protector(password))


def key_der(key: TestKey, *, password: bytes | None = None) -> bytes:
    """Return *key* as PKCS#8 DER, encrypted when a *password* is given."""
    return key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, _protector(password))


def archive(
    certificate: Certificate | None,
    key: TestKey | None,
    *,
    password: bytes | None = None,
) -> bytes:
    """Return a PKCS#12 archive holding the given parts, encrypted on demand."""
    return pkcs12.serialize_key_and_certificates(
        name=b"ksef2",
        key=key,
        cert=certificate,
        cas=None,
        encryption_algorithm=_protector(password),
    )


def public_key_der(key: TestKey) -> bytes:
    """Return the SubjectPublicKeyInfo DER that pairs *key* with a certificate."""
    return key.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    )


def build_credentials(
    certificate: Certificate,
    key: TestKey,
    credential_format: CredentialFormat,
    *,
    password: bytes | None,
) -> XAdESCredentials:
    """Build credentials for *certificate* and *key* in the requested input format."""
    if credential_format == "pem":
        return XAdESCredentials.from_pem(
            certificate.public_bytes(Encoding.PEM),
            key_pem(key, password=password),
            key_password=password,
        )
    if credential_format == "der":
        return XAdESCredentials.from_der(
            certificate.public_bytes(Encoding.DER),
            key_der(key, password=password),
            key_password=password,
        )
    return XAdESCredentials.from_pkcs12(
        archive(certificate, key, password=password), password=password
    )


def _protector(password: bytes | None) -> serialization.KeySerializationEncryption:
    return NoEncryption() if password is None else BestAvailableEncryption(password)
