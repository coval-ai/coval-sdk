# Releasing

The API SDKs use the same release model as [coval-agent-sdk](https://github.com/coval-ai/coval-agent-sdk): pinned Python Semantic Release, Conventional Commit squash titles, generated changelogs, and the Coval Release Automation GitHub App. Each repository has its own version series. Within this repository, Python `coval-sdk` and TypeScript `@coval/sdk` share one version, one `vX.Y.Z` tag, and one changelog.

## Contributor flow

The [PR title workflow](../.github/workflows/pr-title.yml) checks PRs targeting `main` when opened, edited, reopened, synchronized, or marked ready for review. Titles must use `<type>[optional scope][!]: <description>` with one of `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`, or `test`. Squash merges default to the PR title with a blank commit body, so mark breaking changes with `!` in the title, such as `feat(api)!: replace the client`; a footer in the PR description is not carried into the commit. The workflow reads event metadata without checking out PR code or requesting token permissions. After the workflow lands on `main`, add `Conventional Commit title` as a required check in the SDK CI ruleset to block malformed titles from merging.

Squash-merge reviewed PRs using Conventional Commit titles. `fix:` and `perf:` produce a patch, `feat:` produces a minor, and `!` or `BREAKING CHANGE:` produces a major, including `1.0.0` from `0.x`. Maintenance and documentation commits do not release on their own. Generated updates use `fix(sdks):` commits; release preparation follows that Conventional Commit history when its gate is enabled. Changes that require a minor or major release need the corresponding semantic commit before package publication.

Release Automation checks out current `main`, derives the next version, and stamps it into Python package metadata, Python runtime version strings, the npm manifest, and the npm lockfile. It generates `CHANGELOG.md` and creates `chore(release): X.Y.Z` and `vX.Y.Z`. The validator permits only these version changes and the generated changelog, requires an increase beyond both previous package versions, and rejects stale preparation. A read-only preparation job exports the release patch and a hash-bound manifest. A separate `release-automation` environment job checks out the workflow event’s protected-main revision, validates artifact integrity and allowed regular-file paths, reconstructs the commit, and independently validates version-only changes and current-main freshness using the trusted checkout’s standard-library tooling. It installs no dependencies and executes no candidate code. Only then does it mint the scoped App token and push the commit and tag atomically; a concurrent main update cannot be overwritten. The App's `chore(release):` commit does not start another preparation run. Its generated SDK commits can start preparation when the release gate is enabled.

The tag starts `publish.yml`. Before either upload, it validates the App-pushed tag and generated commit in main history, builds and tests both packages, and checks clean package installations. The isolated `pypi` and `npm` jobs then download their respective artifacts and use registry Trusted Publishing with job-scoped OIDC. The npm job uses the Node distribution’s OIDC-capable CLI without installing tooling and publishes with lifecycle scripts disabled. The Python publisher does not check out or execute the SDK.

Regeneration prepares generated source in a read-only job and exports a patch after both validations. A separate protected-main promotion job verifies the expected backend source, base revision, patch hash, regular-file modes, and generated-path allowlist before minting its App token. Artifacts cannot update workflow/tooling files, Git configuration, or symlinks. A concurrent main update rejects promotion; the workflow never rebases generated output. Regeneration accepts only backend `openapi_specs_published` dispatches and uses the same App to commit generated updates directly to `main` after content verification, deterministic generation, and both SDK validations succeed. It downloads the event’s exact public spec set and verifies each hash before generation. Recovery is the backend’s manual **Publish OpenAPI Specs** workflow against the deployed backend commit; SDK regeneration has no cron or manual dispatch. It stages only SDK source and the generated Python README, treats unchanged output as a no-op, and refuses to push if `main` advanced during generation. Failed validations leave `main` unchanged. Inspect the failed Actions run for step logs and recovery guidance in its job summary; regeneration does not use the repository issue tracker. Recovery republishes from the backend; it never force-pushes or rebases output that has not been validated against a new base. It does not bump versions; Semantic Release owns versioning after the generated commit reaches `main`.

## Repository cutover

The import preserves Python `0.9.2` and TypeScript `0.7.2`. Their next semantic release synchronizes them at a version above both: a patch begins at `0.9.3`, a feature at `0.10.0`, and a breaking change at `1.0.0`. Package names, import paths, and runtime APIs remain unchanged by this migration.

The new repository starts with `SDK_REGEN_ENABLED` and `SDK_RELEASES_ENABLED` unset, which disables regeneration, release preparation, and publication. SDK CI remains active.

1. Merge the SDK import and verify CI. Ensure intended source readers can access the new repository before retiring the original source paths. Repository visibility is a separate maintainer decision.
2. Reconcile SDK changes that landed in `coval-examples` after the extraction base, then merge its cleanup to retire the old SDK workflows. Do not enable both repositories' regeneration or release workflows together.
3. Complete the App and Trusted Publisher setup below. Verify the backend publisher dispatch App can write repository events to `coval-sdk`; the Coval Release App owns validated regeneration commits. No docs-repository token is needed.
4. Verify the imported versions against the registries and source repository. While release gates are disabled, establish `v0.9.2` at the imported main revision as the migration baseline. It marks the existing Python release boundary and does not claim that npm published `0.9.2`. Do not copy the old per-language tag schemes. Release Automation refuses to start without a reachable semantic baseline covering both imported version numbers.
5. Land the backend publication-manifest provider and docs consumer changes, then set `SDK_REGEN_ENABLED=true`. Use the backend’s manual publish workflow against the deployed backend SHA and verify the resulting SDK and docs commits, or their explicit no-change outcomes. Dispatch acceptance alone does not establish that either consumer finished successfully. Set `SDK_RELEASES_ENABLED=true` only after App access, publisher identities, the baseline, and the old-workflow retirement are verified. A semantic merge can then publish both packages automatically; use environment approvals if each upload needs a maintainer decision.

No package or tag is published merely by preparing or merging this gated import. Source installs move to `git+https://github.com/coval-ai/coval-sdk.git#subdirectory=python-sdk` once the selected revision is available to the consumer.

## Configure the App and publishers

Install the existing Coval Release Automation GitHub App on `coval-ai/coval-sdk`. It needs Contents write access for release commits/tags and permission to push validated regeneration commits to `main`. Make `RELEASE_AUTOMATION_APP_CLIENT_ID` available as a repository variable. Store this repository’s distinct `RELEASE_AUTOMATION_APP_PRIVATE_KEY` only in the `release-automation` environment, whose deployment branch policy permits exactly the `main` branch. Keep that environment approval-free for automatic releases. Stage the environment key before merging these workflows, then remove the old repository-level copy after the workflow cutover. Never retrieve an encrypted key through a workflow; use the original maintainer key file or an approved replacement. Do not create another App, copy encrypted secrets through workflows, or use a stored registry token. Branch rules must allow the intended App-authored release commit without weakening other protections.

Configure these registry identities before enabling releases:

| Setting | PyPI | npm |
| --- | --- | --- |
| Package | `coval-sdk` | `@coval/sdk` |
| GitHub owner | `coval-ai` | `coval-ai` |
| Repository | `coval-sdk` | `coval-sdk` |
| Workflow filename | `publish.yml` | `publish.yml` |
| GitHub environment | `pypi` | `npm` |

Create those GitHub environments and configure their review/tag policies as appropriate. Permit `v*` tags for normal publication and the exact `main` branch for App-authored recovery events, whose workflow ref is `main` even though the build checks out the release tag. Publication still requires the release App actor and validation of that tag's generated commit in main history. Confirm the `coval-engineering` code-owner team has write access and a working private security reporting channel exists before making the repository public. npm Trusted Publishing supports private source repositories, but npm provenance requires public source. Leave npm's automatic provenance behavior in place; making the source public is a separate decision. See [npm's publisher documentation](https://docs.npmjs.com/trusted-publishers/). Workflow files do not configure App installations, secrets, registry trust, repository visibility, or branch protection.

## Validation and recovery

Use Python 3.12 for release tooling:

```sh
scripts/install
.venv/bin/python -m pytest release_tests -q
npm ci --prefix typescript-sdk
scripts/check
```

The release tests run the real pinned Semantic Release tool against isolated Git remotes. They cover the divergent-version cutover, patch/minor/breaking/no-op behavior, synchronized artifact metadata, invalid release content and tags, and concurrent main updates. Runtime CI retains Python 3.9, 3.12, and 3.14; release tooling is installed separately so it does not change the SDK's runtime Python support.

Before the atomic push, a failed preparation can be retried with manual dispatch from `main`; no manual version bump is needed. After the push, retry failed publishing jobs at the same generated tag. If the workflow itself needs a correction, merge that correction first, then dispatch **Publish SDK packages** from `main` with `release_tag` set to the existing tag (for example, `gh workflow run publish.yml --ref main -f release_tag=v0.9.3`). The maintainer run asks the Coval Release App to dispatch `sdk_release_retry`; only that App-authored event can run publication. The corrected default-branch workflow checks out the immutable tag and applies the same generated-release, main-history, build, and installation validation. PyPI skips existing distributions, and npm skips an existing exact package version. Registry errors other than npm's explicit not-found result fail the job.

The registries cannot commit atomically together. One upload may succeed while the other fails; keep the same tag and version and retry only the incomplete publication. Do not move tags, replace published contents, or increment versions just to retry. A generated changelog or successful build does not establish availability: confirm both registry versions, provenance, and fresh consumer installations before reporting a shared release complete.

## Publication event contract

The backend stages only externally visible specs, publishes them, and independently dispatches `openapi_specs_published` to this repository and docs. `client_payload` contains `schema_version: 1`, `ref` as the resolved 40-character backend commit, and a nonempty `specs` list of `{name, sha256}` entries. SHA-256 values identify the exact staged bytes; names identify resources at `https://api.coval.dev/v1/openapi/{name}`. Duplicate names, invalid metadata, failed requests, or mismatched bytes fail before generated input files change.

Public URLs serve the latest publication; the event does not create persistent immutable snapshots. A later publish or cached response can make verification fail. Republish the intended deployed backend revision through the backend workflow rather than bypassing verification or dispatching a consumer manually. Failed or missed dispatches are also recovered there. Regeneration and package publication remain separate gates.

## Workflow dependencies

Pin maintained Actions to full commit SHAs and update the corresponding version comment when upgrading. Keep checkout credentials unpersisted, keep build jobs read-only, and preserve the separation between candidate preparation, App-authenticated promotion, and registry OIDC upload. Validate workflow policy and artifact rejection cases through the release tests before changing these boundaries.
