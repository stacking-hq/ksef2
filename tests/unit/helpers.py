from base64 import b64encode

VALID_BASE64 = b64encode(b"polyfactory-test-certificate-data").decode()
VALID_CERTIFICATE_ID = b64encode(b"certificate-id-32-byte-value-000").decode()
VALID_PUBLIC_KEY_ID = b64encode(b"public-key-id-32-byte-value-000").decode()
