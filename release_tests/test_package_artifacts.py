"""Exercise the public package-validation command with real archive formats."""

import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("kind", ["wheel", "sdist", "npm"])
@pytest.mark.parametrize("fault", [None, "missing-license", "stale-notice", "wrong-license"])
def test_package_attribution(tmp_path, kind, fault):
    expression = "Apache-2.0" if fault == "wrong-license" else "MIT"
    metadata = f"Metadata-Version: 2.4\nName: synthetic-sdk\nLicense-Expression: {expression}\n\n".encode()
    if kind == "wheel":
        path = tmp_path / "synthetic_sdk-1.0-py3-none-any.whl"
        prefix = "synthetic_sdk-1.0.dist-info/licenses/"
        files = {"synthetic_sdk-1.0.dist-info/METADATA": metadata}
    elif kind == "sdist":
        path = tmp_path / "synthetic_sdk-1.0.tar.gz"
        prefix = "synthetic_sdk-1.0/"
        files = {prefix + "PKG-INFO": metadata}
    else:
        path = tmp_path / "synthetic-sdk-1.0.tgz"
        prefix = "package/"
        files = {prefix + "package.json": json.dumps({"license": expression}).encode()}
    files[prefix + "LICENSE"] = (ROOT / "LICENSE").read_bytes()
    files[prefix + "NOTICE"] = (ROOT / "NOTICE").read_bytes()
    if fault == "missing-license":
        del files[prefix + "LICENSE"]
    elif fault == "stale-notice":
        files[prefix + "NOTICE"] = b"Outdated attribution\n"
    if kind == "wheel":
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
    else:
        with tarfile.open(path, "w:gz") as archive:
            for name, data in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_package.py"), str(path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    if fault is None:
        assert result.returncode == 0, result.stderr
        assert "canonical MIT license and attribution" in result.stdout
    else:
        assert result.returncode != 0
        expected = {
            "missing-license": "missing or stale LICENSE",
            "stale-notice": "missing or stale NOTICE",
            "wrong-license": "expected MIT license metadata",
        }[fault]
        assert expected in result.stderr
