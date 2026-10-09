"""Unit tests for the public XAdES helpers used by certificate authentication."""

import base64
import datetime
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from lxml import etree

from ksef2._core.xades import _AUTH_TOKEN_NS
from ksef2.xades import (
    LocalSigner,
    build_auth_token_request_xml,
    generate_personal_test_certificate,
    generate_test_certificate,
    load_certificate_and_key_from_p12,
    load_certificate_from_pem,
    load_private_key_from_pem,
    sign_xades,
)

ORGANIZATION_IDENTIFIER_OID = x509.ObjectIdentifier("2.5.4.97")
SERIAL_NUMBER_OID = x509.ObjectIdentifier("2.5.4.5")
RSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
ECDSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"


def self_signed(
    private_key: rsa.RSAPrivateKey
    | ec.EllipticCurvePrivateKey
    | ed25519.Ed25519PrivateKey,
) -> x509.Certificate:
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ksef2 xades test")])
    now = datetime.datetime.now(datetime.UTC)
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(hours=1))
        .not_valid_after(now + datetime.timedelta(days=1))
    )
    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        return builder.sign(private_key, None)
    return builder.sign(private_key, hashes.SHA256())


def archive(
    cert: x509.Certificate | None,
    private_key: (
        rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey | ed25519.Ed25519PrivateKey
    ),
    *,
    password: bytes,
) -> bytes:
    return pkcs12.serialize_key_and_certificates(
        name=b"ksef2",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password),
    )


def pem(key: PrivateKeyTypes) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def text(root: etree._Element, tag: str, namespace: str = _AUTH_TOKEN_NS) -> str | None:
    found = root.findall(f".//{{{namespace}}}{tag}")
    return None if not found else found[0].text


def subject_values(cert: x509.Certificate, oid: x509.ObjectIdentifier) -> list[str]:
    return [
        str(attribute.value) for attribute in cert.subject.get_attributes_for_oid(oid)
    ]


@pytest.fixture(scope="module")
def rsa_key_and_cert() -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return self_signed(private_key), private_key


@pytest.fixture(scope="module")
def ec_key_and_cert() -> tuple[x509.Certificate, ec.EllipticCurvePrivateKey]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    return self_signed(private_key), private_key


def test_load_private_key_from_pem_bytes_and_path(
    tmp_path: Path,
    rsa_key_and_cert: tuple[x509.Certificate, rsa.RSAPrivateKey],
) -> None:
    _, private_key = rsa_key_and_cert
    key_pem = pem(private_key)
    path = tmp_path / "key.pem"
    _ = path.write_bytes(key_pem)

    assert load_private_key_from_pem(key_pem).private_numbers() == (
        private_key.private_numbers()
    )
    assert load_private_key_from_pem(path).private_numbers() == (
        private_key.private_numbers()
    )
    assert load_private_key_from_pem(str(path)).private_numbers() == (
        private_key.private_numbers()
    )


def test_load_private_key_decrypts_a_password_protected_pem(tmp_path: Path) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    encrypted = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(b"s3cret"),
    )
    path = tmp_path / "encrypted.key"
    _ = path.write_bytes(encrypted)

    loaded = load_private_key_from_pem(path, password=b"s3cret")

    assert loaded.private_numbers() == private_key.private_numbers()


def test_load_private_key_accepts_elliptic_curve_keys(
    ec_key_and_cert: tuple[x509.Certificate, ec.EllipticCurvePrivateKey],
) -> None:
    _, private_key = ec_key_and_cert

    loaded = load_private_key_from_pem(pem(private_key))

    assert isinstance(loaded, ec.EllipticCurvePrivateKey)


def test_load_private_key_rejects_other_key_types() -> None:
    with pytest.raises(TypeError, match="Expected RSA or EC private key, got Ed25519"):
        load_private_key_from_pem(pem(ed25519.Ed25519PrivateKey.generate()))


def test_load_certificate_from_pem_bytes_and_path(
    tmp_path: Path,
    rsa_key_and_cert: tuple[x509.Certificate, rsa.RSAPrivateKey],
) -> None:
    cert, _ = rsa_key_and_cert
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    path = tmp_path / "cert.pem"
    _ = path.write_bytes(cert_pem)

    assert load_certificate_from_pem(cert_pem) == cert
    assert load_certificate_from_pem(path) == cert


def test_load_certificate_and_key_from_p12(
    rsa_key_and_cert: tuple[x509.Certificate, rsa.RSAPrivateKey],
) -> None:
    cert, private_key = rsa_key_and_cert

    loaded_cert, loaded_key = load_certificate_and_key_from_p12(
        archive(cert, private_key, password=b"hastle"), password=b"hastle"
    )

    assert loaded_cert == cert
    assert loaded_key.private_numbers() == private_key.private_numbers()


def test_load_certificate_and_key_rejects_a_p12_without_a_certificate(
    rsa_key_and_cert: tuple[x509.Certificate, rsa.RSAPrivateKey],
) -> None:
    _, private_key = rsa_key_and_cert
    blob = archive(None, private_key, password=b"hastle")

    with pytest.raises(ValueError, match="No certificate found in PKCS#12 archive"):
        load_certificate_and_key_from_p12(blob, password=b"hastle")


def test_load_certificate_and_key_rejects_an_unusable_key() -> None:
    private_key = ed25519.Ed25519PrivateKey.generate()
    blob = archive(self_signed(private_key), private_key, password=b"hastle")

    with pytest.raises(TypeError, match="Expected RSA or EC private key, got Ed25519"):
        load_certificate_and_key_from_p12(blob, password=b"hastle")


def test_generate_test_certificate_uses_the_company_seal_subject() -> None:
    cert, private_key = generate_test_certificate("1234567890")

    assert subject_values(cert, ORGANIZATION_IDENTIFIER_OID) == ["VATPL-1234567890"]
    assert subject_values(cert, NameOID.COMMON_NAME) == ["KSeF SDK Test"]
    assert subject_values(cert, NameOID.COUNTRY_NAME) == ["PL"]
    assert subject_values(cert, NameOID.ORGANIZATION_NAME) == ["KSeF SDK Test"]
    assert cert.issuer == cert.subject
    assert private_key.key_size == 2048
    assert cert.not_valid_after_utc > cert.not_valid_before_utc


def test_generate_personal_test_certificate_uses_the_pesel_serial_number() -> None:
    cert, _ = generate_personal_test_certificate("44010112345")

    assert subject_values(cert, SERIAL_NUMBER_OID) == ["TINPL-44010112345"]
    assert subject_values(cert, ORGANIZATION_IDENTIFIER_OID) == []
    assert subject_values(cert, NameOID.COMMON_NAME) == ["KSeF SDK Test"]


def test_generate_personal_test_certificate_can_carry_a_representative_nip() -> None:
    cert, _ = generate_personal_test_certificate("44010112345", nip="1234567890")

    assert subject_values(cert, ORGANIZATION_IDENTIFIER_OID) == ["VATPL-1234567890"]
    assert subject_values(cert, SERIAL_NUMBER_OID) == ["TINPL-44010112345"]
    assert str(
        cert.subject.get_attributes_for_oid(ORGANIZATION_IDENTIFIER_OID)[0].oid
    ) == str(ORGANIZATION_IDENTIFIER_OID)


def test_build_auth_token_request_xml_matches_the_auth_schema() -> None:
    payload = build_auth_token_request_xml(challenge="challenge-123", nip="1234567890")
    root = etree.fromstring(payload)

    assert payload.startswith(b"<?xml")
    assert root.tag == f"{{{_AUTH_TOKEN_NS}}}AuthTokenRequest"
    assert text(root, "Challenge") == "challenge-123"
    assert text(root, "Nip") == "1234567890"
    assert text(root, "SubjectIdentifierType") == "certificateSubject"


def test_build_auth_token_request_xml_keeps_a_custom_subject_identifier_type() -> None:
    root = etree.fromstring(
        build_auth_token_request_xml(
            challenge="challenge-123",
            nip="1234567890",
            subject_identifier_type="personalSubject",
        )
    )

    assert text(root, "SubjectIdentifierType") == "personalSubject"


@pytest.mark.parametrize(
    ("key_fixture", "expected_algorithm"),
    [
        ("rsa_key_and_cert", RSA_SHA256),
        ("ec_key_and_cert", ECDSA_SHA256),
    ],
)
def test_sign_xades_produces_an_enveloped_signature(
    request: pytest.FixtureRequest,
    key_fixture: str,
    expected_algorithm: str,
) -> None:
    cert, private_key = request.getfixturevalue(key_fixture)

    signed = sign_xades(
        build_auth_token_request_xml("challenge-123", "1234567890"),
        cert,
        private_key,
    )
    root = etree.fromstring(signed)

    assert root.tag == f"{{{_AUTH_TOKEN_NS}}}AuthTokenRequest"
    assert text(root, "Challenge") == "challenge-123"
    signature = root.findall(f"{{{DS_NS}}}Signature")
    assert len(signature) == 1
    methods = signature[0].findall(
        f"./{{{DS_NS}}}SignedInfo/{{{DS_NS}}}SignatureMethod"
    )
    assert len(methods) == 1
    assert methods[0].get("Algorithm") == expected_algorithm
    embedded = root.findall(f".//{{{DS_NS}}}X509Certificate")
    assert len(embedded) == 1
    assert (
        x509.load_der_x509_certificate(base64.b64decode(embedded[0].text or "")) == cert
    )


def test_local_signer_signs_like_the_module_function(
    rsa_key_and_cert: tuple[x509.Certificate, rsa.RSAPrivateKey],
) -> None:
    cert, private_key = rsa_key_and_cert

    signed = LocalSigner(cert, private_key).sign(
        build_auth_token_request_xml("challenge-123", "1234567890")
    )

    assert etree.fromstring(signed).tag == f"{{{_AUTH_TOKEN_NS}}}AuthTokenRequest"
    assert b"SignatureValue" in signed
