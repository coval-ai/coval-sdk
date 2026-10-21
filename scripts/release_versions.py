"""Own version stamping for the Python and TypeScript release artifacts."""

from __future__ import annotations

import json
import re
import tomllib

VERSION_PATTERN = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
VERSION_FILES = (
    "python-sdk/pyproject.toml",
    "python-sdk/src/coval_sdk/__init__.py",
    "python-sdk/src/coval_sdk/api_client.py",
    "python-sdk/src/coval_sdk/configuration.py",
    "typescript-sdk/package.json",
    "typescript-sdk/package-lock.json",
)


def version_tuple(version: str) -> tuple[int, int, int]:
    """Parse a final version without accepting prereleases or leading zeroes."""
    if not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError("Version must be MAJOR.MINOR.PATCH.")
    return tuple(int(part) for part in version.split("."))


def package_versions(contents: dict[str, str]) -> tuple[str, str]:
    """Read the two public package versions."""
    python = tomllib.loads(contents[VERSION_FILES[0]])["project"]["version"]
    typescript = json.loads(contents["typescript-sdk/package.json"])["version"]
    version_tuple(python)
    version_tuple(typescript)
    return python, typescript


def _replace(pattern: str, replacement: str, contents: str) -> str:
    result, count = re.subn(pattern, replacement, contents, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Expected exactly one version marker: {pattern}")
    return result


def synchronized(contents: dict[str, str], version: str) -> dict[str, str]:
    """Return the exact metadata-only transformation for one shared release."""
    version_tuple(version)
    result = dict(contents)
    result[VERSION_FILES[0]] = _replace(
        r'^version = "[^"]+"$', f'version = "{version}"', contents[VERSION_FILES[0]]
    )
    patterns = {
        "python-sdk/src/coval_sdk/__init__.py": (
            r'^__version__ = "[^"]+"$',
            f'__version__ = "{version}"',
        ),
        "python-sdk/src/coval_sdk/api_client.py": (
            r"OpenAPI-Generator/[0-9.]+/python",
            f"OpenAPI-Generator/{version}/python",
        ),
        "python-sdk/src/coval_sdk/configuration.py": (
            r"SDK Package Version: [0-9.]+",
            f"SDK Package Version: {version}",
        ),
    }
    for name, (pattern, replacement) in patterns.items():
        result[name] = _replace(pattern, replacement, contents[name])
    for name in ("typescript-sdk/package.json", "typescript-sdk/package-lock.json"):
        metadata = json.loads(contents[name])
        metadata["version"] = version
        if name.endswith("package-lock.json"):
            metadata["packages"][""]["version"] = version
        result[name] = json.dumps(metadata, indent=2) + "\n"
    return result
