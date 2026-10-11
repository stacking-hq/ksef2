import base64
import datetime
import hashlib

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.x509.oid import NameOID

from ksef2._core import crypto
from ksef2._core.exceptions import KSeFEncryptionError
from ksef2._domain.models.encryption import PublicKeyCertificate


def _certificate(private_key: rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey) -> str:
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ksef2 test")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    return base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _oaep() -> padding.OAEP:
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )


def test_encrypt_token_round_trips_with_the_private_key(
    rsa_key: rsa.RSAPrivateKey,
) -> None:
    encrypted = crypto.encrypt_token("tok", "123", _certificate(rsa_key))

    plaintext = rsa_key.decrypt(base64.b64decode(encrypted), _oaep())
    assert plaintext == b"tok|123"


def test_encrypt_symmetric_key_round_trips_with_the_private_key(
    rsa_key: rsa.RSAPrivateKey,
) -> None:
    key, _ = crypto.generate_session_key()

    encrypted = crypto.encrypt_symmetric_key(key, _certificate(rsa_key))

    assert rsa_key.decrypt(encrypted, _oaep()) == key


def test_generate_session_key_has_aes_256_and_cbc_iv_sizes() -> None:
    key, iv = crypto.generate_session_key()

    assert (len(key), len(iv)) == (32, 16)
    assert crypto.generate_session_key() != (key, iv)


@pytest.mark.parametrize("size", [0, 1, 15, 16, 17, 1000])
def test_invoice_encryption_round_trips_and_pads_to_block_size(size: int) -> None:
    key, iv = crypto.generate_session_key()
    xml = b"x" * size

    encrypted = crypto.encrypt_invoice(xml, key, iv)

    assert len(encrypted) % 16 == 0
    assert len(encrypted) > size
    assert crypto.decrypt_aes_cbc(encrypted, key, iv) == xml


def test_encrypt_invoice_wraps_invalid_key_sizes() -> None:
    with pytest.raises(KSeFEncryptionError, match="Invoice encryption failed"):
        crypto.encrypt_invoice(b"x", b"short", b"0" * 16)


def test_decrypt_rejects_invalid_padding_and_wrong_keys() -> None:
    # Fixed inputs: a random wrong key decrypts to valid PKCS#7 padding about
    # 1 time in 256, which made this test flaky.
    key = bytes(range(32))
    other_key = bytes(range(32, 64))
    iv = bytes(range(16))
    encrypted = crypto.encrypt_invoice(b"payload", key, iv)

    # With these bytes the wrong key decrypts the single block to garbage whose
    # last byte is 0x1d (29). PKCS#7 padding bytes must be 1..16, so decryption
    # can never succeed by chance. Pin that so a change to the inputs fails here.
    garbage = decrypt_without_unpadding(other_key, iv, encrypted)
    assert garbage[-1] == 0x1D

    with pytest.raises(KSeFEncryptionError, match="AES-CBC decryption failed"):
        crypto.decrypt_aes_cbc(encrypted, other_key, iv)
    with pytest.raises(KSeFEncryptionError, match="AES-CBC decryption failed"):
        crypto.decrypt_aes_cbc(b"not-a-block-multiple", key, iv)


def decrypt_without_unpadding(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    decryptor = crypto.Cipher(
        crypto.algorithms.AES(key), crypto.modes.CBC(iv)
    ).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def test_decrypt_rejects_inconsistent_padding_bytes() -> None:
    key, iv = crypto.generate_session_key()
    # 16 bytes whose last byte claims 5 padding bytes that are not all 5.
    block = bytes(11) + bytes([1, 2, 3, 4, 5])
    cipher = crypto.Cipher(crypto.algorithms.AES(key), crypto.modes.CBC(iv))
    encryptor = cipher.encryptor()
    forged = encryptor.update(block) + encryptor.finalize()

    with pytest.raises(KSeFEncryptionError, match="Invalid PKCS#7 padding"):
        crypto.decrypt_aes_cbc(forged, key, iv)

    zero_pad = encryptor_for(key, iv, bytes(16))
    with pytest.raises(KSeFEncryptionError, match="Invalid PKCS#7 padding byte"):
        crypto.decrypt_aes_cbc(zero_pad, key, iv)


def encryptor_for(key: bytes, iv: bytes, block: bytes) -> bytes:
    encryptor = crypto.Cipher(
        crypto.algorithms.AES(key), crypto.modes.CBC(iv)
    ).encryptor()
    return encryptor.update(block) + encryptor.finalize()


def test_invalid_certificates_are_reported_as_encryption_errors() -> None:
    with pytest.raises(KSeFEncryptionError, match="Failed to load public key"):
        crypto.encrypt_token("t", "1", base64.b64encode(b"not a cert").decode())
    with pytest.raises(KSeFEncryptionError, match="Failed to load public key"):
        crypto.encrypt_symmetric_key(b"k" * 32, "%%%")


def test_encryption_fails_when_the_message_is_too_long_for_the_key(
    rsa_key: rsa.RSAPrivateKey,
) -> None:
    cert = _certificate(rsa_key)

    with pytest.raises(KSeFEncryptionError, match="Token encryption failed"):
        crypto.encrypt_token("x" * 500, "1", cert)
    with pytest.raises(KSeFEncryptionError, match="Symmetric key encryption failed"):
        crypto.encrypt_symmetric_key(b"k" * 500, cert)


def test_non_rsa_certificates_are_rejected() -> None:
    cert = _certificate(ec.generate_private_key(ec.SECP256R1()))

    with pytest.raises(AssertionError, match="Expected RSA public key"):
        crypto.encrypt_token("t", "1", cert)
    with pytest.raises(AssertionError, match="Expected RSA public key"):
        crypto.encrypt_symmetric_key(b"k" * 32, cert)


def test_select_certificate_returns_the_first_match_or_raises() -> None:
    def cert(usage: list[str], serial: str) -> PublicKeyCertificate:
        return PublicKeyCertificate.model_construct(
            certificate="c", usage=usage, public_key_id=serial
        )

    first = cert(["symmetric_key_encryption"], "1")
    second = cert(["ksef_token_encryption"], "2")

    assert crypto.select_certificate([first, second], "ksef_token_encryption") is second
    with pytest.raises(KSeFEncryptionError, match="No certificate found"):
        crypto.select_certificate([first], "ksef_token_encryption")


def test_sha256_b64_matches_hashlib() -> None:
    assert (
        crypto.sha256_b64(b"abc")
        == base64.b64encode(hashlib.sha256(b"abc").digest()).decode()
    )
