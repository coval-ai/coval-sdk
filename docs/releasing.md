# Releasing

Python (`coval-sdk`) and TypeScript (`@coval/sdk`) keep independent versions and tag prefixes: `python-sdk-v<VERSION>` and `typescript-sdk-v<VERSION>`. This extraction preserves Python 0.9.2 and TypeScript 0.7.2; it does not publish a new version.

## Repository cutover

The new repository starts with regeneration and publication disabled. An unset repository variable is treated as disabled. SDK CI still runs on pull requests and `main`.

1. Merge the SDK import and verify its CI. Ensure the intended source readers can access the new repository before retiring the old paths. Keep the new repository's visibility as agreed separately; moving files does not authorize a visibility change.
2. Merge the `coval-examples` cleanup so its SDK source and workflows stop owning generation and releases. Include any SDK changes merged there since extraction before removing that source.
3. Configure `DOCS_REPO_TOKEN` for read access to `coval-ai/docs` and `REGEN_PR_TOKEN` for this repository's regeneration PRs and release tags. Provision credentials through the established administrative path; do not copy or print existing secret values. Create the `sdk-regen-failure` issue label used by the regeneration workflow.
4. Set up the `pypi` GitHub environment. Configure PyPI's trusted publisher for owner `coval-ai`, repository `coval-sdk`, workflow `publish-coval-sdk.yml`, environment `pypi`. Configure npm's trusted publisher for repository `coval-ai/coval-sdk` and workflow `publish-coval-npm.yml`. Verify the registry's repository-visibility requirements before enabling publishing.
5. Before enabling releases, establish baseline tags for already published versions at the imported revision: `python-sdk-v0.9.2` and `typescript-sdk-v0.7.2`. Do this while `SDK_RELEASES_ENABLED` is unset or `false`; these baseline tags must not republish the existing versions. Verify the baseline against the registries and source repository first.
6. Set `SDK_REGEN_ENABLED=true` and manually dispatch regeneration against an exact docs revision. Verify its result and review any generated changes.
7. After the publishers and baseline tags are verified, set `SDK_RELEASES_ENABLED=true`. Both the tagger and publisher jobs require this variable. Keep it disabled while publisher setup is incomplete.

Do not run both repositories' regeneration or release workflows during cutover. Existing registry installations continue to use the same package names. Source installations should use `git+https://github.com/coval-ai/coval-sdk.git#subdirectory=python-sdk` with an accessible revision.

## Release flow

The weekly or manually dispatched regeneration workflow opens a rolling PR and bumps a package's version when its generated source changes. Review compatibility and validation before merging. Hand-written package changes need an explicit version bump following the language guide's versioning policy.

After SDK CI succeeds for current `main`, the release workflow tags versions that have no matching tag. A successful run on an older `main` cannot release a newer commit. Publication workflows verify tag/version agreement and build, test, and inspect each package before registry upload. The Python workflow also supports manual dispatch and is subject to the same publication gate.

A failed upload can be retried at the same tag; first check whether that version is already present in the registry. Never replace published package contents. Confirm the published version and a clean install before reporting release completion.
