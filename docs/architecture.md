# Architecture

This repository owns the Python `coval-sdk` and TypeScript `@coval/sdk` API clients. Applications own their workflows and credentials. The separate [Agent SDK](https://github.com/coval-ai/coval-agent-sdk) owns voice-session orchestration; these packages expose HTTP APIs.

## Package boundaries

Python lives under `python-sdk/src/coval_sdk/`. `api/` and `models/` contain generated operations and models. `api_client.py`, `configuration.py`, and `rest.py` provide generated transport infrastructure. The handwritten `client.py` configures authentication, safe read retries, and pooled-connection expiry; `pagination.py` and `deserialization.py` own their corresponding helpers.

TypeScript lives under `typescript-sdk/src/`. `generated/` contains OpenAPI operations, models, and fetch transport. `CovalClient.ts` assembles the generated API surfaces; `auth.ts`, `retry.ts`, `errors.ts`, `stats.ts`, and `pagination.ts` own handwritten behavior. `index.ts` is the public facade and also exports generated APIs and models.

Keep transport behavior at those owning boundaries. Do not introduce application frameworks, backend imports, or provider clients into either SDK.

## Generation

`scripts/bundle-spec.mjs` combines the selected `coval-ai/docs` contracts with frozen [compatibility specs](../legacy-specs/README.md). Canonical definitions win where they overlap. `.openapi-generator-config/` and `openapitools.json` configure the generators; `scripts/generate-sdks.sh` invokes them and applies `patch-generated-python.py` and `patch-generated-ts.mjs`.

The scripts preserve handwritten modules and synchronize generated API imports/properties in the client facades. Change the source contract or generator patches for generated behavior, then run generation twice to establish determinism. [Contributing](../CONTRIBUTING.md#generate-clients) has the commands.

## Tooling and releases

The root `.venv` holds Python development and release tools; the root `pyproject.toml` is not another published package. Each language directory owns its distribution metadata. `scripts/build` creates and validates Python and npm archives, including their license and attribution files. `scripts/check` adds runtime tests and isolated package installation checks.

The workflows under `.github/workflows/` own SDK CI, regeneration PRs, release preparation, and registry uploads. [Releasing](releasing.md) defines version synchronization, App authentication, validation, cutover gates, and publication retries.
