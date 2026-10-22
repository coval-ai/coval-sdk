"""Bind backend publication verification to the generation workflow."""

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
        "DETERMINISM": "${{ steps.determinism.outcome }}",
        "TYPESCRIPT_VALIDATION": "${{ steps.typescript_validation.outcome }}",
        "PYTHON_VALIDATION": "${{ steps.python_validation.outcome }}",
    }
    assert "always()" not in publish.get("if", "")
    assert "create-pull-request" not in text
    assert "pull-requests" not in workflow["permissions"]
    checkout = next(
        step
        for step in steps
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "main"
    assert "steps.app-token.outputs.token" in checkout["with"]["token"]


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
