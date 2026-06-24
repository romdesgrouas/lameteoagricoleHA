"""Build versioned release archives for the custom component."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "lameteoagricole" / "manifest.json"
DIST = ROOT / "dist"


def main() -> None:
    """Create latest and versioned zip archives."""
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    DIST.mkdir(exist_ok=True)

    zip_paths = [
        DIST / f"lameteoagricoleHA-v{version}.zip",
        DIST / "lameteoagricoleHA-latest.zip",
    ]

    for zip_path in zip_paths:
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
            for path in ROOT.rglob("*"):
                if _should_skip(path):
                    continue
                archive.write(path, path.relative_to(ROOT).as_posix())
        print(zip_path)


def _should_skip(path: Path) -> bool:
    """Return true when a file should not be packaged."""
    parts = set(path.relative_to(ROOT).parts)
    return (
        path.is_dir()
        or ".git" in parts
        or "__pycache__" in parts
        or "dist" in parts
        or path.suffix in {".pyc", ".pyo"}
    )


if __name__ == "__main__":
    main()
