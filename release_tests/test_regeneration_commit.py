"""Exercise generated SDK publication against real isolated Git remotes."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/commit-generated-sdks.sh"
SOURCE = "c6b36c69e67e2c5c13c499c6c94392562a330bd5"
GENERATED = "python-sdk/src/coval_sdk/api/resource.py"


def run(root, *command, check=True, **values):
    environment = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR")
        if key in os.environ
    }
    environment.update(GIT_CONFIG_GLOBAL=os.devnull, **values)
    result = subprocess.run(
        command, cwd=root, env=environment, text=True, capture_output=True
    )
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


def git(root, *arguments):
    return run(root, "git", *arguments).stdout.strip()


@pytest.fixture
def checkout(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote))
    root = tmp_path / "checkout"
    git(tmp_path, "clone", str(remote), str(root))
    git(root, "config", "user.name", "Synthetic maintainer")
    git(root, "config", "user.email", "maintainer@example.test")
    git(root, "config", "commit.gpgsign", "false")
    for name in (
        GENERATED,
        "python-sdk/GENERATED_README.md",
        "typescript-sdk/src/generated/resource.ts",
        "typescript-sdk/src/CovalClient.ts",
        "README.md",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    git(root, "push", "origin", "main")
    return root


def publish(root, **overrides):
    return run(
        root,
        "bash",
        str(SCRIPT),
        check=False,
        **{
            "SOURCE_REF": SOURCE,
            "DETERMINISM": "success",
            "TYPESCRIPT_VALIDATION": "success",
            "PYTHON_VALIDATION": "success",
            **overrides,
        },
    )


def remote_head(root):
    return git(root, "ls-remote", "origin", "refs/heads/main").split()[0]


def test_validated_output_updates_main_without_unrelated_files(checkout):
    previous = remote_head(checkout)
    (checkout / GENERATED).write_text("new operation\n")
    (checkout / "python-sdk/src/coval_sdk/api/new.py").write_text("new model\n")
    (checkout / "typescript-sdk/src/generated/resource.ts").unlink()
    (checkout / "README.md").write_text("unrelated local edit\n")
    (checkout / "unrelated.txt").write_text("untracked\n")
    result = publish(checkout)
    assert result.returncode == 0, result.stderr
    head = remote_head(checkout)
    assert head != previous
    assert git(
        checkout, "diff-tree", "--no-commit-id", "--name-only", "-r", head
    ).splitlines() == [
        "python-sdk/src/coval_sdk/api/new.py",
        GENERATED,
        "typescript-sdk/src/generated/resource.ts",
    ]
    assert git(checkout, "show", f"{head}:{GENERATED}") == "new operation"
    assert git(checkout, "show", f"{head}:README.md") == "original"
    assert (
        git(checkout, "show", "-s", "--format=%an", head)
        == "coval-release-automation[bot]"
    )
    assert SOURCE in git(checkout, "show", "-s", "--format=%B", head)
    assert (checkout / "README.md").read_text() == "unrelated local edit\n"


def test_unchanged_generated_output_is_a_noop(checkout):
    head = remote_head(checkout)
    (checkout / "README.md").write_text("unrelated local edit\n")
    result = publish(checkout)
    assert result.returncode == 0, result.stderr
    assert "no commit needed" in result.stdout
    assert remote_head(checkout) == git(checkout, "rev-parse", "HEAD") == head


@pytest.mark.parametrize(
    "failed", ["DETERMINISM", "TYPESCRIPT_VALIDATION", "PYTHON_VALIDATION"]
)
def test_failed_validation_cannot_publish(checkout, failed):
    head = remote_head(checkout)
    (checkout / GENERATED).write_text("invalid generated output\n")
    result = publish(checkout, **{failed: "failure"})
    assert result.returncode != 0
    assert "must succeed" in result.stderr
    assert remote_head(checkout) == git(checkout, "rev-parse", "HEAD") == head


def test_prestaged_unrelated_changes_cannot_publish(checkout):
    head = remote_head(checkout)
    (checkout / "README.md").write_text("unrelated staged edit\n")
    git(checkout, "add", "README.md")
    result = publish(checkout)
    assert result.returncode != 0
    assert "pre-staged changes" in result.stderr
    assert remote_head(checkout) == head


@pytest.mark.parametrize("timing", ["before-fetch", "before-push"])
def test_concurrent_main_update_is_preserved(checkout, tmp_path, timing):
    initial = remote_head(checkout)
    other = tmp_path / "other"
    git(tmp_path, "clone", str(tmp_path / "remote.git"), str(other))
    git(other, "config", "user.name", "Concurrent maintainer")
    git(other, "config", "user.email", "concurrent@example.test")
    git(other, "config", "commit.gpgsign", "false")
    (other / "README.md").write_text("concurrent main change\n")
    git(other, "add", ".")
    git(other, "commit", "-m", "concurrent main change")
    newer = git(other, "rev-parse", "HEAD")
    if timing == "before-fetch":
        git(other, "push", "origin", "main")
    else:
        # Load the competing object without advancing main until the real push starts.
        git(other, "push", "origin", "HEAD:refs/heads/concurrent")
        hook = checkout / ".git/hooks/pre-push"
        hook.write_text(
            f'#!/bin/sh\ngit --git-dir="{tmp_path / "remote.git"}" update-ref refs/heads/main {newer}\n'
        )
        hook.chmod(0o755)
    (checkout / GENERATED).write_text("generated output\n")
    result = publish(checkout)
    assert result.returncode != 0
    assert remote_head(checkout) == newer
    assert git(other, "show", f"{newer}:README.md") == "concurrent main change"
    if timing == "before-fetch":
        assert "Main changed during generation" in result.stderr
        assert git(checkout, "rev-parse", "HEAD") == initial
    else:
        assert "failed to push" in result.stderr
