"""Tests for Ed25519 manifest signer."""

import os
import stat

import pytest

from bennu_dataset.signer import ManifestSigner


def test_sign_and_verify():
    signer = ManifestSigner.generate()
    data = signer.canonicalize({"mission_id": "test-001"})
    sig = signer.sign(data)
    assert signer.verify(data, sig)


def test_canonicalize_is_deterministic():
    data1 = ManifestSigner.canonicalize({"b": 2, "a": 1})
    data2 = ManifestSigner.canonicalize({"a": 1, "b": 2})
    assert data1 == data2 == '{"a":1,"b":2}'


def test_verify_rejects_tampered():
    signer = ManifestSigner.generate()
    data = signer.canonicalize({"ok": True})
    sig = signer.sign(data)
    assert not signer.verify(data + "tampered", sig)


def test_verify_rejects_invalid_base64():
    signer = ManifestSigner.generate()
    data = signer.canonicalize({"ok": True})
    assert not signer.verify(data, "not-valid-base64!!!")


def test_cross_key_verification_fails():
    """Signature from one key must not verify with another key."""
    signer_a = ManifestSigner.generate()
    signer_b = ManifestSigner.generate()
    data = signer_a.canonicalize({"cross": "key"})
    sig = signer_a.sign(data)
    assert not signer_b.verify(data, sig)


def test_export_and_import_keys(tmp_path):
    signer = ManifestSigner.generate()
    key_path = tmp_path / "drone.key"
    pub_path = tmp_path / "drone.pub"
    signer.export_keys(key_path, pub_path)

    loaded = ManifestSigner.from_files(key_path, pub_path)
    data = ManifestSigner.canonicalize({"round": "trip"})
    sig = signer.sign(data)
    assert loaded.verify(data, sig)


def test_export_sets_private_key_permissions(tmp_path):
    """Private key file must be owner-read/write only (0o600)."""
    signer = ManifestSigner.generate()
    key_path = tmp_path / "drone.key"
    pub_path = tmp_path / "drone.pub"
    signer.export_keys(key_path, pub_path)

    mode = stat.S_IMODE(os.stat(key_path).st_mode)
    assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"


def test_from_files_rejects_mismatched_keys(tmp_path):
    """Loading a private key with a non-matching public key must raise ValueError."""
    signer_a = ManifestSigner.generate()
    signer_b = ManifestSigner.generate()

    key_path = tmp_path / "a.key"
    pub_path_a = tmp_path / "a.pub"
    pub_path_b = tmp_path / "b.pub"

    signer_a.export_keys(key_path, pub_path_a)
    signer_b.export_keys(tmp_path / "b.key", pub_path_b)

    with pytest.raises(ValueError, match="does not match"):
        ManifestSigner.from_files(key_path, pub_path_b)


def test_from_files_rejects_missing_key(tmp_path):
    """Missing key file raises OSError with context."""
    with pytest.raises(OSError, match="Cannot read signing key"):
        ManifestSigner.from_files(tmp_path / "missing.key", tmp_path / "missing.pub")


def test_from_files_rejects_corrupt_key(tmp_path):
    """Corrupt key bytes raise ValueError."""
    key_path = tmp_path / "bad.key"
    pub_path = tmp_path / "bad.pub"
    key_path.write_bytes(b"tooshort")
    pub_path.write_bytes(b"tooshort")
    with pytest.raises(ValueError, match="Invalid signing key"):
        ManifestSigner.from_files(key_path, pub_path)
