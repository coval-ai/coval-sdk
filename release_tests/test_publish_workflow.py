"""Exercise registry retry decisions from the actual publishing workflow."""

import json
import os
import shutil
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


def test_publish_argument_is_a_local_tarball_to_the_real_npm_parser(tmp_path):
    command = next(
        step["run"]
        for step in workflow()["jobs"]["npm"]["steps"]
        if step.get("name") == "Publish package"
    )
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/coval-sdk-0.9.3.tgz").write_bytes(b"package fixture")
    npm_root = Path(shutil.which("npm")).resolve().parents[1]
    parser = npm_root / "node_modules/npm-package-arg"
    binary = tmp_path / "bin"
    binary.mkdir()
    (binary / "npm").write_text(
        "#!/usr/bin/env node\n"
        "const assert = require('node:assert/strict');\n"
        "const fs = require('node:fs');\n"
        "const parse = require(process.env.NPM_ARGUMENT_PARSER);\n"
        "assert.equal(process.argv[2], 'publish');\n"
        "assert.equal(parse(process.argv[3]).type, 'file');\n"
        "assert(fs.existsSync(process.argv[3]));\n"
        "console.log('local tarball');\n"
    )
    (binary / "npm").chmod(0o755)
    environment = {
        **os.environ,
        "PATH": str(binary) + os.pathsep + os.environ["PATH"],
        "NPM_ARGUMENT_PARSER": str(parser),
    }
    result = subprocess.run(
        ["bash", "-e", "-c", command],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "local tarball"


@pytest.mark.parametrize(
    ("reference", "tag", "allowed"),
    [
        ("refs/heads/main", "v0.9.3", True),
        ("refs/heads/feature", "v0.9.3", False),
        ("refs/heads/main", "v0.9.3rc1", False),
        ("refs/heads/main", "v00.9.3", False),
        ("refs/heads/main", "v0.9.3; touch injected", False),
    ],
)
def test_manual_retry_forwards_only_a_final_tag_from_main(
    tmp_path, reference, tag, allowed
):
    steps = workflow()["jobs"]["retry"]["steps"]
    command = "\n".join(step["run"] for step in steps if "run" in step)
    binary = tmp_path / "bin"
    binary.mkdir()
    (binary / "gh").write_text(
        "#!/usr/bin/env python3\nimport json,sys\n"
        "from pathlib import Path\n"
        "Path('request.json').write_text(json.dumps(sys.argv[1:]))\n"
    )
    (binary / "gh").chmod(0o755)
    result = subprocess.run(
        ["bash", "-e", "-c", command],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": str(binary) + os.pathsep + os.environ["PATH"],
            "GITHUB_REF": reference,
            "RELEASE_TAG": tag,
            "GITHUB_REPOSITORY": "coval-ai/coval-sdk",
        },
        text=True,
        capture_output=True,
        check=False,
    )
    request = tmp_path / "request.json"
    if allowed:
        assert result.returncode == 0, result.stderr
        assert json.loads(request.read_text()) == [
            "api",
            "--method",
            "POST",
            "repos/coval-ai/coval-sdk/dispatches",
            "-f",
            "event_type=sdk_release_retry",
            "-f",
            "client_payload[tag]=v0.9.3",
        ]
    else:
        assert result.returncode != 0
        assert not request.exists()
    assert not (tmp_path / "injected").exists()


def test_recovery_uses_app_event_and_checks_out_the_tag_before_validation():
    config = workflow()
    build = config["jobs"]["build"]
    assert "github.actor == 'coval-release-automation[bot]'" in build["if"]
    assert "github.event_name != 'workflow_dispatch'" in build["if"]
    assert config["env"]["RELEASE_TAG"] == (
        "${{ github.event.client_payload.tag || github.ref_name }}"
    )
    checkout = next(
        step
        for step in build["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "refs/tags/${{ env.RELEASE_TAG }}"
    validation = next(
        step
        for step in build["steps"]
        if step.get("name") == "Verify generated release tag"
    )
    assert 'validate_release.py tag "$RELEASE_TAG"' in validation["run"]
    retry = config["jobs"]["retry"]
    token = next(step for step in retry["steps"] if step.get("id") == "app-token")
    assert token["with"]["permission-contents"] == "write"
    dispatch = next(
        step
        for step in retry["steps"]
        if step.get("name") == "Dispatch existing release"
    )
    assert dispatch["env"]["GH_TOKEN"] == "${{ steps.app-token.outputs.token }}"
