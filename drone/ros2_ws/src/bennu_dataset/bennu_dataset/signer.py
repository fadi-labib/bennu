"""Ed25519 manifest signing for Bennu mission bundles."""

import base64
import binascii
import json
import os
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey


class ManifestSigner:
    """Signs and verifies manifest JSON using Ed25519."""

    def __init__(self, signing_key: SigningKey):
        self._signing_key = signing_key
        self._verify_key = signing_key.verify_key

    @classmethod
    def generate(cls) -> "ManifestSigner":
        """Generate a new random keypair."""
        return cls(SigningKey.generate())

    @classmethod
    def from_files(cls, key_path: Path, pub_path: Path) -> "ManifestSigner":
        """Load keypair from files."""
        key_path = Path(key_path)
        pub_path = Path(pub_path)

        try:
            key_bytes = key_path.read_bytes()
        except OSError as e:
            raise OSError(f"Cannot read signing key from {key_path}: {e}") from e
        try:
            pub_bytes = pub_path.read_bytes()
        except OSError as e:
            raise OSError(f"Cannot read public key from {pub_path}: {e}") from e

        try:
            signing_key = SigningKey(key_bytes)
        except Exception as e:
            raise ValueError(
                f"Invalid signing key in {key_path} (expected 32 raw bytes): {e}"
            ) from e
        try:
            stored_pub = VerifyKey(pub_bytes)
        except Exception as e:
            raise ValueError(
                f"Invalid public key in {pub_path} (expected 32 raw bytes): {e}"
            ) from e

        if signing_key.verify_key.encode() != stored_pub.encode():
            raise ValueError(f"Public key {pub_path} does not match private key {key_path}")
        return cls(signing_key)

    def export_keys(self, key_path: Path, pub_path: Path) -> None:
        """Save keypair to files. Private key is written with 0o600 permissions."""
        key_path = Path(key_path)
        pub_path = Path(pub_path)

        # Write to temp files first, then rename for atomicity
        key_tmp = key_path.with_suffix(".key.tmp")
        pub_tmp = pub_path.with_suffix(".pub.tmp")
        try:
            # Create private key with restrictive permissions
            fd = os.open(str(key_tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(fd, bytes(self._signing_key))
            finally:
                os.close(fd)
            pub_tmp.write_bytes(bytes(self._verify_key))
            key_tmp.rename(key_path)
            pub_tmp.rename(pub_path)
        except OSError:
            key_tmp.unlink(missing_ok=True)
            pub_tmp.unlink(missing_ok=True)
            raise

    @staticmethod
    def canonicalize(data: dict) -> str:
        """Deterministic JSON: sorted keys, compact separators."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def sign(self, data_str: str) -> str:
        """Sign a string, return base64-encoded signature."""
        signed = self._signing_key.sign(data_str.encode())
        return base64.b64encode(signed.signature).decode()

    def verify(self, data_str: str, signature_b64: str) -> bool:
        """Verify a base64-encoded signature against data."""
        try:
            sig_bytes = base64.b64decode(signature_b64, validate=True)
        except binascii.Error:
            return False
        try:
            self._verify_key.verify(data_str.encode(), sig_bytes)
            return True
        except BadSignatureError:
            return False

    @property
    def public_key_bytes(self) -> bytes:
        """Raw public key bytes (32 bytes)."""
        return bytes(self._verify_key)
