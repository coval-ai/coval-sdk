"""Stamp PSR's NEW_VERSION into both packages before its release commit."""

import os
from pathlib import Path

import release_versions


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    contents = {
        name: (root / name).read_text() for name in release_versions.VERSION_FILES
    }
    version = os.environ["NEW_VERSION"]
    if release_versions.package_versions(contents)[0] != version:
        raise ValueError("Semantic Release must stamp the Python version first.")
    updated = release_versions.synchronized(contents, version)
    for name, text in updated.items():
        (root / name).write_text(text)


if __name__ == "__main__":
    main()
