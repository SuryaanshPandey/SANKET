"""Test cryptographic hash integrity and immutability."""

import hashlib
import io
import pytest
from PIL import Image

from clarity.preprocessing.pipeline import run_preprocessing_pipeline
from clarity.storage import compute_sha256, LocalStorageBackend, get_hashed_storage_path


def create_test_image_bytes(text: str = "Evidence Document") -> bytes:
    """Generate sample image bytes."""
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_hash_immutability_through_preprocessing(tmp_path):
    """Verify that preprocessing never alters original bytes or original hash."""
    original_bytes = create_test_image_bytes("Contract Agreement")
    original_hash = compute_sha256(original_bytes)

    # Store original
    storage = LocalStorageBackend(base_dir=tmp_path / "storage")
    raw_key = get_hashed_storage_path(original_hash, prefix="raw", extension="png")
    stored_path = storage.put_bytes(raw_key, original_bytes)

    # Run preprocessing
    prep_result = run_preprocessing_pipeline(original_bytes)

    # Store preprocessed derivative separately
    prep_key = get_hashed_storage_path(original_hash, prefix="preprocessed", extension="png")
    prep_stored_path = storage.put_bytes(prep_key, prep_result.preprocessed_bytes)

    # Retrieve stored raw bytes and verify hash
    retrieved_raw = storage.get_bytes(raw_key)
    retrieved_hash = compute_sha256(retrieved_raw)

    assert retrieved_hash == original_hash, "Original file hash changed in storage!"
    assert retrieved_raw == original_bytes, "Original bytes were mutated in storage!"

    # Verify preprocessed derivative is distinct
    assert prep_stored_path != stored_path
    assert prep_result.preprocessed_bytes != original_bytes
    assert compute_sha256(prep_result.preprocessed_bytes) != original_hash
