"""Exercise registry retry decisions from the actual publishing workflow."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow():
    return yaml.safe_load((ROOT / ".github/workflows/publish.yml").read_text())


@pytest.mark.parametrize(
    ("response", "exit_code", "expected"),
    [
        ("0.9.3", 0, "publish=false\n"),
        ({"error": {"code": "E404"}}, 1, "publish=true\n"),
        ({"error": {"code": "E401"}}, 1, None),
        ({"error": {"code": "E503"}}, 1, None),
        ("0.9.4", 0, None),
    ],
)
def test_npm_retry_checks_exact_version_and_only_accepts_explicit_not_found(
    tmp_path, response, exit_code, expected
):
    commands = [
        step["run"]
        for step in workflow()["jobs"]["npm"]["steps"]
        if step.get("id") == "registry"
    ]
    assert len(commands) == 1
    binary = tmp_path / "bin"
    binary.mkdir()
    (binary / "npm").write_text(
        "#!/bin/sh\n"
        '[ "$1" = view ] && [ "$2" = "@coval/sdk@0.9.3" ] || exit 99\n'
        "cat <<'JSON'\n" + json.dumps(response) + "\nJSON\n"
        f"exit {exit_code}\n"
    )
    (binary / "npm").chmod(0o755)
    output = tmp_path / "output"
    output.write_text("")
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "TMPDIR"}
    }
    environment.update(
        PATH=str(binary) + os.pathsep + environment["PATH"],
        RELEASE_TAG="v0.9.3",
        GITHUB_OUTPUT=str(output),
    )
    result = subprocess.run(
        ["bash", "-e", "-c", commands[0]],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if expected is None:
        assert result.returncode != 0
        assert output.read_text() == ""
    else:
        assert result.returncode == 0, result.stderr
        assert output.read_text() == expected


def test_both_registry_jobs_require_the_shared_validated_artifacts():
    config = workflow()
    jobs = config["jobs"]
    assert "SDK_RELEASES_ENABLED" in jobs["build"]["if"]
    assert "id-token" not in config["permissions"]
    assert "id-token" not in jobs["build"].get("permissions", {})
    assert any(step.get("run") == "scripts/check" for step in jobs["build"]["steps"])
    uploads = {
        step["with"]["name"]
        for step in jobs["build"]["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact@")
    }
    assert uploads == {"coval-sdk-python", "coval-sdk-npm"}
    for registry, artifact in [("pypi", "coval-sdk-python"), ("npm", "coval-sdk-npm")]:
        job = jobs[registry]
        assert job["needs"] == "build"
        assert job["permissions"]["id-token"] == "write"
        assert any(
            step.get("with", {}).get("name") == artifact for step in job["steps"]
        )
        assert not any(
            step.get("uses", "").startswith("actions/checkout@")
            for step in job["steps"]
        )
    assert any(
        step.get("with", {}).get("skip-existing") is True
        for step in jobs["pypi"]["steps"]
    )
    assert any(
        step.get("if") == "steps.registry.outputs.publish == 'true'"
        and step.get("run", "").startswith("npm publish ")
        for step in jobs["npm"]["steps"]
    )
