from __future__ import annotations

import hashlib
from pathlib import Path


def file_hash_checker(file_path: str, algorithm: str = "sha256") -> str:
    path = Path(file_path or "").expanduser()
    if not path.exists() or not path.is_file():
        return f"Hash alinacak dosya bulunamadi: {path}"
    algorithm = (algorithm or "sha256").lower()
    if algorithm not in hashlib.algorithms_available:
        return f"Desteklenmeyen hash algoritmasi: {algorithm}"
    h = hashlib.new(algorithm)
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return "\n".join([
            "DOSYA HASH RAPORU",
            f"Dosya: {path}",
            f"Boyut: {path.stat().st_size} byte",
            f"Algoritma: {algorithm}",
            f"Hash: {h.hexdigest()}",
        ])
    except Exception as exc:
        return f"Hash hesaplama hatasi: {exc}"
