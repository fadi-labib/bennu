"""Ed25519 manifest signing for Bennu mission bundles."""
import base64
import json
from pathlib import Path

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
        signing_key = SigningKey(Path(key_path).read_bytes())
        # Verify the public key matches
        stored_pub = VerifyKey(Path(pub_path).read_bytes())
        assert signing_key.verify_key.encode() == stored_pub.encode(), \
            "Public key file does not match private key"
        return cls(signing_key)

    def export_keys(self, key_path: Path, pub_path: Path) -> None:
        """Save keypair to files."""
        Path(key_path).write_bytes(bytes(self._signing_key))
        Path(pub_path).write_bytes(bytes(self._verify_key))

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
            sig_bytes = base64.b64decode(signature_b64)
            self._verify_key.verify(data_str.encode(), sig_bytes)
            return True
        except Exception:
            return False

    @property
    def public_key_bytes(self) -> bytes:
        """Raw public key bytes (32 bytes)."""
        return bytes(self._verify_key)
