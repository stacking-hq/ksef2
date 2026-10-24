"""Unit tests for XAdESCredentials, the loaded credentials of with_xades()."""

import base64
import json
from typing import Literal
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa, ec, ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import BaseModel
from signxml.xades import XAdESVerifier

from ksef2._core.exceptions import KSeFArgumentError
from ksef2._core.xades import build_auth_token_request_xml, sign_xades
from ksef2.models import XAdESCredentials
from ksef2.xades import XAdESCredentials as FacadeXAdESCredentials
from tests.unit.support.xades_material import (
    CredentialFormat,
    archive,
    build_credentials,
    key_der,
    key_pem,
    public_key_der,
    self_signed,
)

SENTINEL_PASSWORD = b"sentinel-key-password-do-not-keep"
OTHER_SENTINEL_PASSWORD = b"another-sentinel-password-do-not-keep"


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def ec_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def other_rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.mark.parametrize("credential_format", ["pem", "der", "pkcs12"])
@pytest.mark.parametrize("key_kind", ["rsa", "ec"], ids=["rsa", "ec"])
@pytest.mark.parametrize("encrypted", [False, True], ids=["plain", "password"])
def test_credentials_support_all_formats(
    credential_format: CredentialFormat,
    key_kind: Literal["rsa", "ec"],
    encrypted: bool,
    rsa_key: rsa.RSAPrivateKey,
    ec_key: ec.EllipticCurvePrivateKey,
) -> None:
    key: PrivateKeyTypes = rsa_key if key_kind == "rsa" else ec_key
    password = SENTINEL_PASSWORD if encrypted else None
    certificate = self_signed(key)

    credentials = build_credentials(
        certificate, key, credential_format, password=password
    )
    signing_cert, signing_key = credentials.certificate, credentials.private_key

    assert signing_cert.public_bytes(Encoding.DER) == certificate.public_bytes(
        Encoding.DER
    )
    assert public_key_der(signing_key) == public_key_der(key)


@pytest.mark.parametrize("credential_format", ["pem", "der", "pkcs12"])
@pytest.mark.parametrize("key_kind", ["rsa", "ec"], ids=["rsa", "ec"])
def test_resolved_material_signs_a_real_xades_payload(
    credential_format: CredentialFormat,
    key_kind: Literal["rsa", "ec"],
    rsa_key: rsa.RSAPrivateKey,
    ec_key: ec.EllipticCurvePrivateKey,
) -> None:
    """The key the holder hands the signer is the one KSeF can verify on the cert."""
    key: PrivateKeyTypes = rsa_key if key_kind == "rsa" else ec_key
    certificate = self_signed(key)
    credentials = build_credentials(certificate, key, credential_format, password=None)

    signing_cert, signing_key = credentials.certificate, credentials.private_key
    signed = sign_xades(
        build_auth_token_request_xml("challenge-value", "1234567890"),
        signing_cert,
        signing_key,
    )

    verified = XAdESVerifier().verify(signed, x509_cert=signing_cert)
    assert verified[0].signed_xml is not None
    challenge = verified[0].signed_xml.find(
        "{http://ksef.mf.gov.pl/auth/token/2.0}Challenge"
    )
    assert challenge is not None
    assert challenge.text == "challenge-value"
    assert b"X509Data" in signed
    assert certificate.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    ) == public_key_der(signing_key)
    assert signing_cert.fingerprint(hashes.SHA256()) == certificate.fingerprint(
        hashes.SHA256()
    )


def test_encrypted_input_keeps_loaded_key_without_password_or_input_bytes(
    rsa_key: rsa.RSAPrivateKey,
) -> None:
    """Neither the password nor the ciphertext survives the constructor."""
    certificate = self_signed(rsa_key)
    encrypted_pem = key_pem(rsa_key, password=SENTINEL_PASSWORD)

    credentials = XAdESCredentials.from_pem(
        certificate.public_bytes(Encoding.PEM),
        encrypted_pem,
        key_password=SENTINEL_PASSWORD,
    )

    assert public_key_der(credentials.private_key) == public_key_der(rsa_key)
    assert not hasattr(credentials, "__dict__")
    assert not hasattr(credentials, "key_password")
    assert not hasattr(credentials, "key_pem")


def test_credentials_reject_invalid_material(
    rsa_key: rsa.RSAPrivateKey,
    ec_key: ec.EllipticCurvePrivateKey,
    other_rsa_key: rsa.RSAPrivateKey,
) -> None:
    """Every unreadable or unusable input fails as KSeFArgumentError, before network."""
    certificate = self_signed(rsa_key)
    ec_certificate = self_signed(ec_key)
    ed25519_key = ed25519.Ed25519PrivateKey.generate()
    dsa_key = dsa.generate_private_key(key_size=2048)

    def reject(operation: object, *, from_loader: bool = True) -> KSeFArgumentError:
        with pytest.raises(KSeFArgumentError) as exc_info:
            operation()  # pyright: ignore[reportCallIssue]
        error = exc_info.value
        if from_loader:
            assert isinstance(error.__cause__, (ValueError, TypeError))
        else:
            assert error.__cause__ is None
        return error

    assert "certificate" in str(
        reject(
            lambda: XAdESCredentials.from_pem(
                b"not a certificate at all", key_pem(rsa_key)
            )
        )
    )
    assert "certificate" in str(
        reject(lambda: XAdESCredentials.from_pem(b"", key_pem(rsa_key)))
    )
    assert "certificate" in str(
        reject(lambda: XAdESCredentials.from_pem(key_pem(rsa_key), key_pem(rsa_key)))
    )
    assert "private key" in str(
        reject(
            lambda: XAdESCredentials.from_pem(
                certificate.public_bytes(Encoding.PEM), b"not a private key"
            )
        )
    )
    assert "DER" in str(
        reject(
            lambda: XAdESCredentials.from_der(
                certificate.public_bytes(Encoding.DER)[:120], key_der(rsa_key)
            )
        )
    )
    assert "password" in str(
        reject(
            lambda: XAdESCredentials.from_pem(
                certificate.public_bytes(Encoding.PEM),
                key_pem(rsa_key, password=SENTINEL_PASSWORD),
            )
        )
    )
    assert "password" in str(
        reject(
            lambda: XAdESCredentials.from_pem(
                certificate.public_bytes(Encoding.PEM),
                key_pem(rsa_key),
                key_password=SENTINEL_PASSWORD,
            )
        )
    )
    assert "DER" in str(
        reject(
            lambda: XAdESCredentials.from_der(
                certificate.public_bytes(Encoding.DER),
                key_pem(rsa_key),
            )
        )
    )

    wrong_p12_password = reject(
        lambda: XAdESCredentials.from_pkcs12(
            archive(certificate, rsa_key, password=SENTINEL_PASSWORD),
            password=OTHER_SENTINEL_PASSWORD,
        )
    )
    assert "PKCS#12" in str(wrong_p12_password)
    assert SENTINEL_PASSWORD.decode() not in str(wrong_p12_password.context)

    assert "PKCS#12" in str(
        reject(
            lambda: XAdESCredentials.from_pkcs12(
                archive(certificate, rsa_key, password=SENTINEL_PASSWORD)
            )
        )
    )
    assert "no private key" in str(
        reject(
            lambda: XAdESCredentials.from_pkcs12(archive(certificate, None)),
            from_loader=False,
        )
    )
    assert "no certificate" in str(
        reject(
            lambda: XAdESCredentials.from_pkcs12(archive(None, rsa_key)),
            from_loader=False,
        )
    )
    assert "Ed25519PrivateKey" in str(
        reject(
            lambda: XAdESCredentials.from_pem(
                self_signed(ed25519_key).public_bytes(Encoding.PEM),
                key_pem(ed25519_key),
            ),
            from_loader=False,
        )
    )
    assert "DSAPrivateKey" in str(
        reject(
            lambda: XAdESCredentials.from_pkcs12(
                archive(self_signed(dsa_key), dsa_key)
            ),
            from_loader=False,
        )
    )
    assert "does not belong" in str(
        reject(
            lambda: XAdESCredentials.from_pem(
                certificate.public_bytes(Encoding.PEM), key_pem(other_rsa_key)
            ),
            from_loader=False,
        )
    )
    assert "does not belong" in str(
        reject(
            lambda: XAdESCredentials.from_der(
                ec_certificate.public_bytes(Encoding.DER), key_der(rsa_key)
            ),
            from_loader=False,
        )
    )


def test_mismatched_pair_never_reaches_a_request_for_any_format(
    rsa_key: rsa.RSAPrivateKey, other_rsa_key: rsa.RSAPrivateKey
) -> None:
    """PEM and DER can carry a mismatched pair; a PKCS#12 archive cannot be built."""
    certificate = self_signed(rsa_key)

    with pytest.raises(KSeFArgumentError, match="does not belong"):
        _ = XAdESCredentials.from_pem(
            certificate.public_bytes(Encoding.PEM), key_pem(other_rsa_key)
        )
    with pytest.raises(KSeFArgumentError, match="does not belong"):
        _ = XAdESCredentials.from_der(
            certificate.public_bytes(Encoding.DER), key_der(other_rsa_key)
        )
    with pytest.raises(ValueError, match="do not match"):
        _ = archive(certificate, other_rsa_key)


@pytest.mark.parametrize("credential_format", ["pem", "der", "pkcs12"])
@pytest.mark.parametrize("encrypted", [False, True], ids=["plain", "password"])
def test_rejections_never_carry_secret_material(
    credential_format: CredentialFormat,
    encrypted: bool,
    rsa_key: rsa.RSAPrivateKey,
    other_rsa_key: rsa.RSAPrivateKey,
) -> None:
    """Messages, context and repr of a failure show no key bytes and no password."""
    certificate = self_signed(rsa_key)
    password = SENTINEL_PASSWORD if encrypted else None

    # Every format is fed the same secret inputs together with a key that is not the
    # certificate's. A PKCS#12 archive cannot be built from a mismatched pair, so its
    # archive is correct and is read back with the wrong password instead.
    with pytest.raises(KSeFArgumentError) as exc_info:
        if credential_format == "pkcs12":
            _ = XAdESCredentials.from_pkcs12(
                archive(certificate, rsa_key, password=SENTINEL_PASSWORD),
                password=OTHER_SENTINEL_PASSWORD if encrypted else None,
            )
        else:
            encode = key_pem if credential_format == "pem" else key_der
            to_bytes = (
                certificate.public_bytes(Encoding.PEM)
                if credential_format == "pem"
                else certificate.public_bytes(Encoding.DER)
            )
            wrong_key = encode(
                other_rsa_key, password=SENTINEL_PASSWORD if encrypted else None
            )
            if credential_format == "pem":
                _ = XAdESCredentials.from_pem(
                    to_bytes, wrong_key, key_password=password
                )
            else:
                _ = XAdESCredentials.from_der(
                    to_bytes, wrong_key, key_password=password
                )
    error = exc_info.value

    rendered = " ".join([str(error), repr(error), str(error.context), str(error.args)])
    for secret in (
        SENTINEL_PASSWORD.decode(),
        OTHER_SENTINEL_PASSWORD.decode(),
        key_pem(other_rsa_key, password=SENTINEL_PASSWORD).decode(errors="replace"),
        base64.b64encode(key_pem(other_rsa_key, password=SENTINEL_PASSWORD)).decode(),
    ):
        assert secret not in rendered
    assert error.context["code"] == "ARGUMENT_ERROR"


def test_credentials_redact_private_material(rsa_key: rsa.RSAPrivateKey) -> None:
    certificate = self_signed(rsa_key)
    credentials = XAdESCredentials.from_pem(
        certificate.public_bytes(Encoding.PEM),
        key_pem(rsa_key, password=SENTINEL_PASSWORD),
        key_password=SENTINEL_PASSWORD,
    )
    assert repr(credentials) == "XAdESCredentials(<redacted>)"
    assert str(credentials) == "XAdESCredentials(<redacted>)"
    with pytest.raises(TypeError):
        json.dumps(credentials)
    assert not issubclass(XAdESCredentials, BaseModel)
    assert not hasattr(credentials, "model_dump")
    assert not hasattr(credentials, "model_json_schema")
    assert type(credentials) is XAdESCredentials is FacadeXAdESCredentials


def test_loaded_objects_are_retained_and_validated_once(
    rsa_key: rsa.RSAPrivateKey,
) -> None:
    certificate = self_signed(rsa_key)
    from ksef2._domain.models import xades

    with patch.object(xades, "_usable_pair", wraps=xades._usable_pair) as validate:
        credentials = XAdESCredentials(certificate, rsa_key)
        assert credentials.certificate is certificate
        assert credentials.private_key is rsa_key
        assert credentials.private_key is credentials.private_key
        validate.assert_called_once_with(certificate, rsa_key)

    with pytest.raises(AttributeError):
        credentials.private_key = rsa_key  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(AttributeError):
        credentials.certificate = certificate  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("credential_format", ["pem", "der", "pkcs12"])
def test_loaded_material_is_not_reparsed_for_signing(
    credential_format: CredentialFormat, rsa_key: rsa.RSAPrivateKey
) -> None:
    from ksef2._domain.models import xades

    certificate = self_signed(rsa_key)
    with patch.object(xades, "_usable_pair", wraps=xades._usable_pair) as validate:
        credentials = build_credentials(
            certificate, rsa_key, credential_format, password=None
        )
        validate.assert_called_once()
    with (
        patch.object(xades, "_usable_pair", side_effect=AssertionError("revalidated")),
        patch.object(
            xades.x509,
            "load_pem_x509_certificate",
            side_effect=AssertionError("reparsed certificate"),
        ),
        patch.object(
            xades.serialization,
            "load_pem_private_key",
            side_effect=AssertionError("reparsed key"),
        ),
    ):
        signed = sign_xades(
            build_auth_token_request_xml("challenge-value", "1234567890"),
            credentials.certificate,
            credentials.private_key,
        )
    assert b"SignatureValue" in signed


def test_direct_constructor_rejects_unusable_pairs(
    rsa_key: rsa.RSAPrivateKey, other_rsa_key: rsa.RSAPrivateKey
) -> None:
    with pytest.raises(KSeFArgumentError, match="does not belong"):
        XAdESCredentials(self_signed(rsa_key), other_rsa_key)
    unsupported_key = ed25519.Ed25519PrivateKey.generate()
    with pytest.raises(KSeFArgumentError, match="Ed25519PrivateKey"):
        XAdESCredentials(self_signed(unsupported_key), unsupported_key)
