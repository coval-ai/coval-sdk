# AGENTS.md

Instructions for coding agents working on the Coval API SDKs. The closest applicable `AGENTS.md` governs its directory; explicit user instructions take precedence. Follow existing authorization without asking for it again.

## Before you start

- Read `README.md` for the supported packages and developer API.
- Read `CONTRIBUTING.md` before changing code or preparing a pull request.
- Read `AGENTS.meta.md` before editing either agent-guidance file.
- Read `docs/python-style.md` or `docs/typescript-style.md` before changing the corresponding language.
- Read `docs/architecture.md` before moving responsibilities or changing generation.
- Read `docs/runtime.md` before changing authentication, retries, connections, errors, or pagination.
- Read `docs/developer-api.md` before changing public exports or compatibility surfaces.

## Commands

- Run `scripts/install` from the repository root to install the editable Python SDK and release tools.
- Run `npm ci --prefix scripts` for generation tools and `npm ci --prefix typescript-sdk` for TypeScript tools.
- Run `scripts/check` after runtime, entry-point, dependency, or packaging changes; it builds both distributions and tests clean installations.
- Run `scripts/build` when a consumer needs local packages; validate artifacts without publishing them.
- Check local links and run `git diff --check` for documentation-only changes; run broader checks only when affected behavior warrants them.
- Follow `CONTRIBUTING.md` for focused language checks and generation commands.

## Package and generated code

- Keep Python `coval-sdk` / `coval_sdk` and TypeScript `@coval/sdk` identities and supported public APIs stable.
- Preserve Python 3.9+ and Node.js 18+ runtime compatibility separately from development-tool requirements.
- Keep generated clients in `python-sdk/src/coval_sdk/api`, `python-sdk/src/coval_sdk/models`, and `typescript-sdk/src/generated`.
- Fix generation through the source contract or scripts rather than editing output that regeneration erases.
- Preserve handwritten wrappers, compatibility specs, dependency pins, and regression assertions during extraction.
- Keep provider frameworks, application configuration, and consumer source paths outside these packages.
- Update language READMEs, public documentation, and affected examples when a supported interface changes.
- Keep package copies of `LICENSE` and `NOTICE` identical to the root files; `scripts/build` checks their archive contents and MIT metadata.

## Tests and runtime

- Use synthetic fixtures and deterministic local collaborators for automated tests; live API calls need an explicitly selected environment and existing authorization.
- Preserve coverage for authentication, retry eligibility, request serialization, response validation, pagination, and public exports.
- Keep the behavior under test real and substitute collaborators at their owning external boundaries.
- Exercise installed-package boundaries without modifying `sys.path`.
- Distinguish local, mocked, and hosted evidence; do not infer a successful API operation from a successful request launch.
- Never commit credentials, connection tokens, customer data, audio, or transcripts.

## Documentation and comments

- Follow `CONTRIBUTING.md` for document ownership, comment purpose, and prose review.
- Search guidance, templates, docs, and examples for changed commands or APIs and update affected claims in the same change.
- Keep technical explanations in their owning docs page and link to them instead of duplicating them.
- Write Markdown paragraphs on one line while preserving structured lists, tables, and code blocks.

## Releases and security

- Follow `docs/releasing.md` before changing release tooling, publishing, or enabling migration gates.
- Use Conventional Commit PR titles and squash merges; Semantic Release owns both package versions, `CHANGELOG.md`, and `vX.Y.Z` tags.
- Run `scripts/install` and `.venv/bin/python -m pytest release_tests -q` on Python 3.12 after changing release tooling.
- Obtain explicit authorization before publishing packages or changing repository visibility.
- Preserve an existing pull request's draft state unless the user authorizes changing it.
- Follow `SECURITY.md` for vulnerability reports and keep sensitive reproduction details out of public issues.
