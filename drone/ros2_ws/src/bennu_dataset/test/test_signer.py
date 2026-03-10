"""Tests for Ed25519 manifest signer."""
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


def test_export_and_import_keys(tmp_path):
    signer = ManifestSigner.generate()
    key_path = tmp_path / "drone.key"
    pub_path = tmp_path / "drone.pub"
    signer.export_keys(key_path, pub_path)

    loaded = ManifestSigner.from_files(key_path, pub_path)
    data = ManifestSigner.canonicalize({"round": "trip"})
    sig = signer.sign(data)
    assert loaded.verify(data, sig)
