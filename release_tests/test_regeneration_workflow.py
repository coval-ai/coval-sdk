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
    pr = next(
        step
        for step in steps
        if step.get("uses", "").startswith("peter-evans/create-pull-request@")
    )
    assert "${{ github.event.client_payload.ref }}" in pr["with"]["body"]
    assert "steps.app-token.outputs.token" in pr["with"]["token"]
