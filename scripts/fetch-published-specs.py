"""Download and verify the public spec set named by a backend publish event."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Callable
import urllib.request


BASE_URL = "https://api.coval.dev/v1/openapi"


class PublicationError(ValueError):
    """The event or downloaded bytes do not identify one backend publication."""


def publication(event: dict) -> tuple[str, list[tuple[str, str]]]:
    """Validate the publication identity and every spec before making requests."""
    payload = event.get("client_payload", {})
    if (
        not isinstance(payload, dict)
        or type(payload.get("schema_version")) is not int
        or payload["schema_version"] != 1
    ):
        raise PublicationError("Expected backend publication schema_version=1")
    source = payload.get("ref")
    if (
        not isinstance(source, str)
        or re.fullmatch(r"[0-9a-f]{40}", source) is None
    ):
        raise PublicationError("Expected the resolved backend commit SHA")
    specs = payload.get("specs")
    if not isinstance(specs, list) or not specs:
        raise PublicationError("Expected a nonempty backend spec manifest")
    result = []
    seen = set()
    for entry in specs:
        if not isinstance(entry, dict):
            raise PublicationError("Invalid backend spec entry")
        name, digest = entry.get("name"), entry.get("sha256")
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) is None
            or name in seen
        ):
            raise PublicationError("Invalid or duplicate public spec name")
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise PublicationError(f"Invalid SHA-256 for public spec {name}")
        seen.add(name)
        result.append((name, digest))
    return source, result


def fetch_spec(name: str) -> bytes:
    """Read a spec from the fixed public API origin without credentials."""
    request = urllib.request.Request(
        f"{BASE_URL}/{name}",
        headers={"Accept": "application/yaml", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def download(
    event: dict, destination: Path, fetch: Callable[[str], bytes] = fetch_spec
) -> str:
    """Verify the complete input set before replacing managed spec files."""
    source, specs = publication(event)
    verified = {}
    for name, digest in specs:
        data = fetch(name)
        if hashlib.sha256(data).hexdigest() != digest:
            raise PublicationError(
                f"Public spec {name} differs from backend {source}; "
                "rerun the backend Publish OpenAPI Specs workflow"
            )
        verified[f"{name}-v1.yaml"] = data
    destination.mkdir(parents=True, exist_ok=True)
    for old in destination.glob("*-v1.yaml"):
        old.unlink()
    for name, data in verified.items():
        (destination / name).write_bytes(data)
    return source


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    source = download(event, arguments.output)
    print(f"Verified published OpenAPI specs from backend {source}")
