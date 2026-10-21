"""Validate license metadata and attribution in built SDK distributions."""

from __future__ import annotations

import email.parser
import json
from pathlib import Path
import sys
import tarfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def validate_artifact(path: Path, root: Path = ROOT) -> None:
    """Require canonical legal files and MIT metadata in one built archive."""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        metadata_name = next(name for name in files if name.endswith(".dist-info/METADATA"))
        prefix = metadata_name.removesuffix("METADATA") + "licenses/"
        metadata = email.parser.BytesParser().parsebytes(files[metadata_name])
        license_expression = metadata["License-Expression"]
    else:
        with tarfile.open(path, "r:gz") as archive:
            files = {}
            for member in archive.getmembers():
                if member.isfile():
                    stream = archive.extractfile(member)
                    if stream is not None:
                        files[member.name] = stream.read()
        if path.suffix == ".tgz":
            prefix = "package/"
            license_expression = json.loads(files[prefix + "package.json"])["license"]
        else:
            metadata_name = next(name for name in files if name.count("/") == 1 and name.endswith("/PKG-INFO"))
            prefix = metadata_name.removesuffix("PKG-INFO")
            metadata = email.parser.BytesParser().parsebytes(files[metadata_name])
            license_expression = metadata["License-Expression"]
    if license_expression != "MIT":
        raise ValueError(f"{path.name}: expected MIT license metadata")
    for name in ("LICENSE", "NOTICE"):
        if files.get(prefix + name) != (root / name).read_bytes():
            raise ValueError(f"{path.name}: missing or stale {name}")


if __name__ == "__main__":
    artifacts = [Path(name) for name in sys.argv[1:]]
    if not artifacts:
        artifacts = [
            *ROOT.glob("dist/python/*.whl"),
            *ROOT.glob("dist/python/*.tar.gz"),
            *ROOT.glob("dist/npm/*.tgz"),
        ]
        if len(artifacts) != 3:
            raise ValueError("Build exactly one wheel, source archive, and npm archive first")
    for artifact in artifacts:
        validate_artifact(artifact)
    print("Built distributions contain canonical MIT license and attribution files.")
