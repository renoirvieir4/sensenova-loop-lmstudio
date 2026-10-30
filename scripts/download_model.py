#!/usr/bin/env python3
"""Download the pinned, validated GGUF and verify its checksum."""
import argparse
import hashlib
from pathlib import Path

REPO = "notfakerv/SenseNova-Loop-9B-Preview-GGUF"
REVISION = "b54ee83643a4e8066290d3062e1a218139c4c007"
FILENAME = "SenseNova-Loop-9B-Preview-Q8_0.gguf"
SHA256 = "7981be1e6e0d03b9f11bfc3b73eefa1a07a9e227acbac5402ee52b5dc8b82d68"
SIZE = 15069056512


def verify(path):
    if path.stat().st_size != SIZE:
        raise ValueError(f"Wrong model size: {path.stat().st_size}; expected {SIZE}")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != SHA256:
        raise ValueError(f"Checksum mismatch: {actual}")
    print(f"Verified {path}\nSHA256: {actual}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-dir", type=Path, default=Path.home() / ".lmstudio/models")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    destination = args.models_dir.expanduser() / "sensenova/SenseNova-Loop-9B-Preview-GGUF"
    path = destination / FILENAME
    if not args.verify_only:
        from huggingface_hub import hf_hub_download
        destination.mkdir(parents=True, exist_ok=True)
        hf_hub_download(REPO, FILENAME, revision=REVISION, local_dir=destination)
    verify(path)


if __name__ == "__main__":
    main()
