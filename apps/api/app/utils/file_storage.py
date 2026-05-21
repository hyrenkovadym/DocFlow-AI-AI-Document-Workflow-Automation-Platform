from pathlib import Path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)
