"""Bind backend publication verification to the generation workflow."""

import os
import subprocess
from pathlib import Path

import yaml


def test_backend_event_is_the_only_regeneration_entry_point():
    root = Path(__file__).resolve().parents[1]
    text = (root / ".github/workflows/regenerate-sdks.yml").read_text()
    workflow = yaml.load(text, Loader=yaml.BaseLoader)
    assert workflow["on"] == {
        "repository_dispatch": {"types": ["openapi_specs_published"]}
    }
    job = workflow["jobs"]["regenerate"]
    assert job["if"] == "vars.SDK_REGEN_ENABLED == 'true'"
    steps = job["steps"]
    fetch_index = next(
        index
        for index, step in enumerate(steps)
        if "fetch-published-specs.py" in step.get("run", "")
    )
    bundle_index = next(
        index for index, step in enumerate(steps) if step.get("id") == "bundle"
    )
    assert fetch_index < bundle_index
    assert (
        steps[bundle_index]["env"]["COVAL_SPECS_DIR"]
        == "${{ github.workspace }}/dist/openapi-specs"
    )
    assert "DOCS_REPO_TOKEN" not in text and "docs_ref" not in text
    assert "repository: coval-ai/docs" not in text
    publish = next(
        step
        for step in steps
        if step.get("run") == "bash scripts/commit-generated-sdks.sh"
    )
    assert steps.index(publish) > next(
        index
        for index, step in enumerate(steps)
        if step.get("id") == "python_validation"
    )
    assert publish["env"] == {
        "SOURCE_REF": "${{ github.event.client_payload.ref }}",
        "CANDIDATE_DIR": "${{ runner.temp }}/generation-candidate",
        "DETERMINISM": "${{ steps.determinism.outcome }}",
        "TYPESCRIPT_VALIDATION": "${{ steps.typescript_validation.outcome }}",
        "PYTHON_VALIDATION": "${{ steps.python_validation.outcome }}",
    }
    assert "always()" not in publish.get("if", "")
    assert "create-pull-request" not in text
    assert workflow["permissions"] == {"contents": "read"}
    assert "permissions" not in job
    checkout = next(
        step
        for step in steps
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    assert checkout["with"]["persist-credentials"] == "false"
    assert "secrets." not in str(job)
    promoter = workflow["jobs"]["promote"]
    assert promoter["environment"] == "release-automation"
    assert "scripts/install" not in str(promoter)
    assert "npm ci" not in str(promoter)
    assert "needs.regenerate.outputs.changed == 'true'" in promoter["if"]
    token_index = next(i for i, step in enumerate(promoter["steps"]) if step.get("id") == "app-token")
    validation_index = next(i for i, step in enumerate(promoter["steps"]) if "release_candidate.py prepare" in step.get("run", ""))
    assert validation_index < token_index


def test_regeneration_failure_appends_recovery_guidance_to_job_summary(tmp_path):
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.load(
        (root / ".github/workflows/regenerate-sdks.yml").read_text(),
        Loader=yaml.BaseLoader,
    )
    step = next(
        step
        for step in workflow["jobs"]["regenerate"]["steps"]
        if "GITHUB_STEP_SUMMARY" in step.get("run", "")
    )
    assert step["if"] == "failure()"
    assert step["env"]["RUN_URL"] == (
        "${{ github.server_url }}/${{ github.repository }}"
        "/actions/runs/${{ github.run_id }}"
    )
    summary = tmp_path / "summary.md"
    summary.write_text("Prior validation details\n")
    run_url = "https://github.com/coval-ai/coval-sdk/actions/runs/12345"
    subprocess.run(
        ["bash", "-e", "-c", step["run"]],
        env={**os.environ, "RUN_URL": run_url, "GITHUB_STEP_SUMMARY": str(summary)},
        check=True,
        capture_output=True,
        text=True,
    )
    result = summary.read_text()
    assert result.startswith("Prior validation details\n")
    assert "SDK regeneration failed" in result
    assert run_url in result
    assert "failed step's logs" in result
    assert "Publish OpenAPI Specs" in result
    assert "deployed backend revision" in result


def test_release_recursion_guard_allows_regeneration_bot_commits():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.load(
        (root / ".github/workflows/release-automation.yml").read_text(),
        Loader=yaml.BaseLoader,
    )
    condition = workflow["jobs"]["release"]["if"]
    assert "vars.SDK_RELEASES_ENABLED == 'true'" in condition
    assert "github.actor !=" not in condition
    assert "!(github.actor == 'coval-release-automation[bot]' &&" in condition
    assert (
        "startsWith(github.event.head_commit.message, 'chore(release):')"
        in condition
    )
