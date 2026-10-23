"""Exercise actual Semantic Release commits and dual-package publication guards."""

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / ".venv/bin/semantic-release"
VALIDATOR = ROOT / "scripts/validate_release.py"
VERSION_FILES = (
    "python-sdk/pyproject.toml",
    "python-sdk/src/coval_sdk/__init__.py",
    "python-sdk/src/coval_sdk/api_client.py",
    "python-sdk/src/coval_sdk/configuration.py",
    "typescript-sdk/package.json",
    "typescript-sdk/package-lock.json",
)


def run(repository, *command, check=True, **values):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "TMPDIR"}
    }
    environment.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        HTTP_PROXY="http://127.0.0.1:9",
        HTTPS_PROXY="http://127.0.0.1:9",
        **values,
    )
    result = subprocess.run(
        command,
        cwd=repository,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


def git(repository, *arguments):
    return run(repository, "git", *arguments).stdout.strip()


def commit(repository, message):
    git(repository, "add", ".")
    git(repository, "commit", "-m", message)


@pytest.fixture
def repository(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", str(remote))
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    git(checkout, "init", "-b", "main")
    git(checkout, "config", "user.name", "Synthetic release test")
    git(checkout, "config", "user.email", "test@example.test")
    git(checkout, "config", "commit.gpgsign", "false")
    for name in [
        *VERSION_FILES,
        "pyproject.toml",
        "CHANGELOG.md",
        ".gitignore",
        "scripts/release_versions.py",
        "scripts/sync_versions.py",
    ]:
        target = checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / name).read_text())
    config = checkout / "pyproject.toml"
    config.write_text(
        config.read_text().replace(
            "https://github.com/coval-ai/coval-sdk.git",
            "https://github.com/example/sdk-release-fixture.git",
        )
    )
    python_metadata = checkout / VERSION_FILES[0]
    python_metadata.write_text(
        re.sub(
            r'(?m)^version = "[0-9]+\.[0-9]+\.[0-9]+"$',
            'version = "0.9.2"',
            python_metadata.read_text(),
        )
    )
    run(checkout, sys.executable, "scripts/sync_versions.py", NEW_VERSION="0.9.2")
    for name in VERSION_FILES[4:]:
        path = checkout / name
        package = json.loads(path.read_text())
        package["version"] = "0.7.2"
        if "packages" in package:
            package["packages"][""]["version"] = "0.7.2"
        path.write_text(json.dumps(package, indent=2) + "\n")
    (checkout / "CHANGELOG.md").write_text("# Changelog\n")
    (checkout / ".venv/bin").mkdir(parents=True)
    (checkout / ".venv/bin/python").symlink_to(sys.executable)
    commit(checkout, "chore: import existing sdk packages")
    git(checkout, "tag", "v0.9.2")
    git(checkout, "remote", "add", "origin", str(remote))
    git(checkout, "push", "-u", "origin", "main")
    return checkout


def prepare(repository):
    output = repository.parent / "release-output"
    output.write_text("")
    run(
        repository,
        str(TOOL),
        "version",
        "--no-push",
        "--no-vcs-release",
        GITHUB_OUTPUT=str(output),
    )
    return output.read_text()


def validate(repository, tag=None, mode="prepared", actor=""):
    arguments = [sys.executable, str(VALIDATOR), mode]
    if tag:
        arguments.append(tag)
    return run(repository, *arguments, check=False, GITHUB_ACTOR=actor)


def assert_versions(repository, version):
    assert (
        tomllib.loads((repository / VERSION_FILES[0]).read_text())["project"]["version"]
        == version
    )
    assert f'__version__ = "{version}"' in (repository / VERSION_FILES[1]).read_text()
    assert (
        f"OpenAPI-Generator/{version}/python"
        in (repository / VERSION_FILES[2]).read_text()
    )
    assert (
        f"SDK Package Version: {version}" in (repository / VERSION_FILES[3]).read_text()
    )
    package = json.loads((repository / VERSION_FILES[4]).read_text())
    lock = json.loads((repository / VERSION_FILES[5]).read_text())
    assert (
        package["version"]
        == lock["version"]
        == lock["packages"][""]["version"]
        == version
    )
    assert package["name"] == "@coval/sdk"
    assert (
        package["devDependencies"]
        == json.loads((ROOT / VERSION_FILES[4]).read_text())["devDependencies"]
    )


def test_cutover_patch_minor_breaking_and_noop(repository):
    assert (
        tomllib.loads((repository / VERSION_FILES[0]).read_text())["project"]["version"]
        == "0.9.2"
    )
    assert json.loads((repository / VERSION_FILES[4]).read_text())["version"] == "0.7.2"
    assert validate(repository, mode="baseline").returncode == 0
    cases = [
        ("fix: synchronize client releases", "0.9.3", "Synchronize client releases"),
        ("perf: reuse API connections", "0.9.4", "Reuse API connections"),
        ("feat: add a resource", "0.10.0", "Add a resource"),
        ("feat!: replace an API", "1.0.0", "Replace an API"),
        (
            "fix: require settings\n\nBREAKING CHANGE: callers must supply settings",
            "2.0.0",
            "Require settings",
        ),
    ]
    for index, (message, version, note) in enumerate(cases):
        (repository / "synthetic.txt").write_text(str(index))
        commit(repository, message)
        git(repository, "push", "origin", "main")
        output = prepare(repository)
        assert "released=true\n" in output
        assert f"tag=v{version}\n" in output
        assert_versions(repository, version)
        assert (
            git(repository, "log", "-1", "--format=%s") == f"chore(release): {version}"
        )
        assert note in (repository / "CHANGELOG.md").read_text()
        result = validate(repository, f"v{version}")
        assert result.returncode == 0, result.stderr
        git(repository, "push", "--atomic", "origin", "HEAD:main", f"v{version}")
        result = validate(
            repository, f"v{version}", "tag", "coval-release-automation[bot]"
        )
        assert result.returncode == 0, result.stderr
    (repository / "notes.txt").write_text("Synthetic documentation.\n")
    commit(repository, "docs: clarify setup")
    git(repository, "push", "origin", "main")
    head = git(repository, "rev-parse", "HEAD")
    changelog = (repository / "CHANGELOG.md").read_text()
    assert "released=false\n" in prepare(repository)
    assert "released=false\n" in prepare(repository)
    assert git(repository, "rev-parse", "HEAD") == head
    assert (repository / "CHANGELOG.md").read_text() == changelog


@pytest.fixture
def prepared(repository):
    (repository / "synthetic.txt").write_text("Synthetic change.\n")
    commit(repository, "fix: preserve a response")
    git(repository, "push", "origin", "main")
    prepare(repository)
    control = validate(repository, "v0.9.3")
    assert control.returncode == 0, control.stderr
    return repository


def test_missing_baseline_cannot_restart_versions_below_published_packages(repository):
    git(repository, "tag", "-d", "v0.9.2")
    assert "migration baseline" in validate(repository, mode="baseline").stderr
    (repository / "synthetic.txt").write_text("Synthetic first release.\n")
    commit(repository, "fix: attempt release without a baseline")
    git(repository, "push", "origin", "main")
    output = prepare(repository)
    assert "tag=v0.0.1\n" in output
    assert "advance beyond both" in validate(repository, "v0.0.1").stderr


@pytest.mark.parametrize("tag", ["v0.9.4", "v00.9.3", "v0.9.3rc1"])
def test_rejects_wrong_or_nonfinal_tag(prepared, tag):
    assert validate(prepared, tag).returncode != 0


@pytest.mark.parametrize("name", VERSION_FILES)
def test_rejects_any_unsynchronized_version(prepared, name):
    path = prepared / name
    path.write_text(path.read_text().replace("0.9.3", "0.9.8"))
    result = validate(prepared, "v0.9.3")
    assert "match every package and runtime version" in result.stderr


@pytest.mark.parametrize("change", ["runtime", "dependency", "source", "changelog"])
def test_rejects_nonversion_release_changes(prepared, change):
    if change == "runtime":
        path = prepared / VERSION_FILES[2]
        path.write_text(
            path.read_text() + "\nraise RuntimeError('unexpected release code')\n"
        )
    elif change == "dependency":
        path = prepared / VERSION_FILES[4]
        path.write_text(
            path.read_text().replace('"typescript": "5.9.3"', '"typescript": "5.9.4"')
        )
    elif change == "source":
        (prepared / "unexpected.py").write_text("raise RuntimeError\n")
    else:
        (prepared / "CHANGELOG.md").write_text("# Missing release notes\n")
    git(prepared, "add", ".")
    git(prepared, "commit", "--amend", "--no-edit")
    git(prepared, "tag", "-f", "v0.9.3")
    result = validate(prepared, "v0.9.3")
    reason = {
        "runtime": "limited to version metadata",
        "dependency": "limited to version metadata",
        "source": "only update all versions",
        "changelog": "generated changelog entry",
    }[change]
    assert reason in result.stderr


def test_rejects_unpublished_tag_wrong_actor_dirty_and_stale_release(prepared):
    assert "release App" in validate(prepared, "v0.9.3", "tag", "jakelevi").stderr
    assert (
        validate(prepared, "v0.9.3", "tag", "coval-release-automation[bot]").returncode
        != 0
    )
    (prepared / "scratch.txt").write_text("Synthetic uncommitted change.\n")
    assert "clean checkout" in validate(prepared, "v0.9.3").stderr
    (prepared / "scratch.txt").unlink()
    git(prepared, "update-ref", "refs/remotes/origin/main", "HEAD")
    assert "current main" in validate(prepared, "v0.9.3").stderr


def test_atomic_push_preserves_remote_main_and_omits_tag_on_concurrent_change(prepared):
    concurrent = prepared.parent / "concurrent"
    git(
        prepared.parent,
        "clone",
        "-b",
        "main",
        str(prepared.parent / "remote.git"),
        str(concurrent),
    )
    git(concurrent, "config", "user.name", "Synthetic other author")
    git(concurrent, "config", "user.email", "other@example.test")
    git(concurrent, "config", "commit.gpgsign", "false")
    (concurrent / "other.txt").write_text("Synthetic concurrent change.\n")
    commit(concurrent, "docs: document settings")
    git(concurrent, "push", "origin", "main")
    result = run(
        prepared,
        "git",
        "push",
        "--atomic",
        "origin",
        "HEAD:main",
        "v0.9.3",
        check=False,
    )
    assert result.returncode != 0
    assert git(prepared, "ls-remote", "--tags", "origin") == ""
    assert git(prepared, "ls-remote", "--heads", "origin", "main").split()[0] == git(
        concurrent, "rev-parse", "HEAD"
    )


def test_rejects_tag_target_and_nonapp_release_author(prepared):
    git(prepared, "tag", "-f", "v0.9.3", "HEAD^")
    assert "checked-out release commit" in validate(prepared, "v0.9.3").stderr
    git(
        prepared,
        "commit",
        "--amend",
        "--no-edit",
        "--author=Synthetic user <user@example.test>",
    )
    git(prepared, "tag", "-f", "v0.9.3")
    assert "authored by the release App" in validate(prepared, "v0.9.3").stderr
