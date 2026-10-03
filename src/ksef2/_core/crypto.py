import base64
import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_der_x509_certificate

from ksef2._core.exceptions import KSeFEncryptionError
from ksef2._domain.models.encryption import PublicKeyCertificate, CertUsage


def _load_public_key(cert_b64: str):
    """Load an RSA public key from a Base64-encoded DER certificate."""
    try:
        cert_der = base64.b64decode(cert_b64)
        cert = load_der_x509_certificate(cert_der)
        return cert.public_key()
    except Exception as exc:
        raise KSeFEncryptionError(
            f"Failed to load public key from certificate: {exc}"
        ) from exc


def select_certificate(
    certificates: list[PublicKeyCertificate], usage: CertUsage
) -> PublicKeyCertificate:
    """Select the first valid certificate matching *usage*.

    *usage* should be ``"ksef_token_encryption"`` or ``"symmetric_key_encryption"``.
    """
    for cert in certificates:
        if usage in cert.usage:
            return cert
    raise KSeFEncryptionError(f"No certificate found with usage={usage!r}")


def encrypt_token(token: str, timestamp: str, cert_b64: str) -> str:
    """RSA-OAEP encrypt ``token|timestamp`` and return Base64.

    Args:
        token: KSeF token.
        timestamp: Challenge timestamp in Unix milliseconds, as a string.
        cert_b64: Base64-encoded DER certificate containing the RSA public key.

    Returns:
        The Base64-encoded ciphertext.

    Raises:
        KSeFEncryptionError: If the certificate cannot be loaded or encryption fails.
    """
    plaintext = f"{token}|{timestamp}".encode()
    public_key = _load_public_key(cert_b64)
    assert isinstance(public_key, rsa.RSAPublicKey), "Expected RSA public key"
    try:
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise KSeFEncryptionError(f"Token encryption failed: {exc}") from exc
    return base64.b64encode(ciphertext).decode()


def generate_session_key() -> tuple[bytes, bytes]:
    """Generate a random AES-256 key (32 bytes) and IV (16 bytes).

    Returns:
        A tuple of the AES key and the initialization vector.
    """
    return os.urandom(32), os.urandom(16)


def encrypt_symmetric_key(key: bytes, cert_b64: str) -> bytes:
    """RSA-OAEP encrypt an AES key with a KSeF public-key certificate.

    Args:
        key: AES key to encrypt.
        cert_b64: Base64-encoded DER certificate containing the RSA public key.

    Returns:
        The raw ciphertext bytes. The caller is responsible for Base64 encoding.

    Raises:
        KSeFEncryptionError: If the certificate cannot be loaded or encryption fails.
    """
    public_key = _load_public_key(cert_b64)
    assert isinstance(public_key, rsa.RSAPublicKey), "Expected RSA public key"
    try:
        ciphertext = public_key.encrypt(
            key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise KSeFEncryptionError(f"Symmetric key encryption failed: {exc}") from exc
    return ciphertext


def encrypt_invoice(xml_bytes: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-256-CBC encrypt *xml_bytes* with PKCS#7 padding.

    Args:
        xml_bytes: Plain invoice XML bytes.
        key: 32-byte AES-256 key.
        iv: 16-byte initialization vector.

    Returns:
        The raw ciphertext bytes. The caller is responsible for Base64 encoding.

    Raises:
        KSeFEncryptionError: If encryption fails, for example because of an invalid key length.
    """
    try:
        # PKCS#7 padding
        block_size = 16
        pad_len = block_size - (len(xml_bytes) % block_size)
        padded = xml_bytes + bytes([pad_len] * pad_len)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()
    except Exception as exc:
        raise KSeFEncryptionError(f"Invoice encryption failed: {exc}") from exc


def decrypt_aes_cbc(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-256-CBC decrypt *ciphertext* and strip PKCS#7 padding.

    Returns the plaintext bytes.
    """
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

        # Strip PKCS#7 padding
        pad_len = decrypted_padded[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError(f"Invalid PKCS#7 padding byte: {pad_len}")
        if decrypted_padded[-pad_len:] != bytes([pad_len] * pad_len):
            raise ValueError("Invalid PKCS#7 padding")
        return decrypted_padded[:-pad_len]
    except KSeFEncryptionError:
        raise
    except Exception as exc:
        raise KSeFEncryptionError(f"AES-CBC decryption failed: {exc}") from exc


def sha256_b64(data: bytes) -> str:
    """Return the SHA-256 digest of *data* as a Base64-encoded string.

    Args:
        data: Bytes to hash.

    Returns:
        The Base64-encoded digest.
    """
    return base64.b64encode(hashlib.sha256(data).digest()).decode()
