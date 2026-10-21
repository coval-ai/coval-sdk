# Contributing

The [README](README.md) introduces the SDKs and their supported packages. This guide describes contribution and review; [Python conventions](docs/python-style.md), [TypeScript conventions](docs/typescript-style.md), and [architecture](docs/architecture.md) describe code ownership.

Use a feature branch from `main` and open a pull request describing the behavior and validation. Keep package identities and existing public APIs stable across maintenance changes. Squash-merge using a Conventional Commit PR title; `fix:`/`perf:` release a patch, `feat:` a minor, and `!`/`BREAKING CHANGE:` a major. Semantic Release owns both package versions, the changelog, and release tags. Do not bump versions in feature or regeneration PRs.

## Pull requests

1. Identify the owning module and whether the change belongs in handwritten code, the source contract, or generation tooling.
2. Implement the behavior and add focused coverage for supported and failure cases.
3. Run relevant checks below and describe unavailable or unrelated failures accurately.
4. Explain the problem, resulting behavior, evidence, and compatibility or migration implications in the PR; link its covering issue.
5. Have the change reviewed before merging and keep unsettled experiments in draft.

## Setup and checks

Use Python 3.12, Node.js 22 or newer, and Java 21 for code generation. The packages retain their supported Python 3.9+ and Node.js 18+ ranges.

For the shared development environment, run `scripts/install` and `npm ci --prefix typescript-sdk`; see [local development](docs/local-development.md). `scripts/check` builds both distributions, checks metadata and legal files, and tests clean installations. Publishing uses these entry points; language CI retains its supported-interpreter matrix and focused commands.

From the repository root:

```sh
python3 -m venv python-sdk/.venv
python-sdk/.venv/bin/python -m pip install -e './python-sdk[dev]'
python-sdk/.venv/bin/python -m pytest python-sdk/tests
python-sdk/.venv/bin/python -m build python-sdk
python-sdk/.venv/bin/python -m twine check python-sdk/dist/*
npm ci --prefix typescript-sdk
npm run build --prefix typescript-sdk
npm test --prefix typescript-sdk
(cd typescript-sdk && npm pack --dry-run)
```

For release workflow, configuration, or version-stamping changes, run `scripts/install` and `.venv/bin/python -m pytest release_tests -q` on Python 3.12. Run `scripts/check` after `npm ci --prefix typescript-sdk` to validate both SDKs and their built packages. Release tools use the root `.venv`; the language-only commands above remain available.

Run checks for the affected SDK. CI also tests Python 3.9, 3.12, and 3.14. Use synthetic inputs and local collaborators; automated checks do not need Coval credentials.

## Generate clients

Clone `coval-ai/docs` alongside this repository, or set `COVAL_SPECS_DIR` to its `api-reference/v1` directory. Record the exact docs commit when reporting generation results.

```sh
npm ci --prefix scripts
node scripts/bundle-spec.mjs
bash scripts/generate-sdks.sh
```

The generator combines the current docs contract with frozen [compatibility specs](legacy-specs/README.md). It preserves hand-written Python modules and patches generated clients and wrapper exports. Change the generation scripts or their source contract for generated-code fixes, then regenerate; keep wrapper changes in their owning modules. Run generation twice and compare the outputs to check determinism.

Do not mix an API refresh with a repository move. Retain existing tests and dependency pins during extraction. Registry publication and migration prerequisites are documented in [Releasing](docs/releasing.md).

## Tests and dependencies

Assert observable requests, results, errors, retries, pagination, serialization, and resource state. Keep the owner under test real and substitute only external boundaries needed for deterministic tests. Use populated values and otherwise-valid inputs so rejection cases fail for the intended reason.

Keep tests outside production source and exercise installed-package boundaries without changing `sys.path`. Preserve distinct failure cases and public exports; do not hide affected failures with skips, weaker assertions, or broader mocks. Use synthetic fixtures without live API calls. Label local, mocked, and hosted evidence accurately.

Add dependencies only for concrete runtime or development requirements. Preserve supported interpreter ranges and declare packages imported directly. Review upgrades as code changes, including distribution/license implications, and retain generated compatibility contracts. Keep framework integrations and application configuration outside the core SDKs.

## Where prose lives

- `README.md` introduces installation and points to the language usage guides.
- `python-sdk/README.md` and `typescript-sdk/README.md` document supported usage and examples.
- `AGENTS.md` contains concise agent instructions; `AGENTS.meta.md` governs their maintenance.
- `CONTRIBUTING.md` describes the human contribution and review workflow.
- `docs/python-style.md` and `docs/typescript-style.md` define language conventions and their enforcement limits.
- `docs/architecture.md` maps responsibilities, generation, and dependency boundaries.
- `docs/developer-api.md` explains public surfaces and compatibility.
- `docs/runtime.md` explains authentication, retries, responses, connections, and pagination.
- `docs/local-development.md` explains editable installs, builds, and consumer checks.
- `docs/releasing.md` owns release setup, cutover, retries, and publishing evidence.
- `SECURITY.md` describes private vulnerability reporting.

Keep explanations in one owning document and link to them elsewhere. Write Markdown paragraphs on one line while retaining structured code blocks, lists, and tables.

## Documentation and comments

Document current behavior and decisions a developer needs to use or change it. Write a comment when a constraint, dependency pin, ordering rule, wire contract, or workaround has a reason the code cannot express. Place it immediately above that code and describe the condition for removing a workaround.

Leave out comments that repeat a name or statement, banners, duplicated explanations, and delivery-history narration. Delete the comment mentally: if no useful information disappears, remove it; otherwise consider whether a clearer name, type, or structure can express the constraint. Rule-specific tool suppressions may remain inline with their concrete reason.

Search guidance, templates, README files, docs, and examples when commands or APIs change. Verify local links, anchors, and examples against implemented behavior, and distinguish proposals or prerequisites from completed behavior. Python public docstrings use meaningful Google-style sections; TypeScript uses JSDoc where it explains the contract. Comments and docstrings follow each language's conventions rather than Markdown's paragraph rule.

## Security and conduct

Follow [SECURITY.md](SECURITY.md) for vulnerabilities. For ordinary bugs or feature requests, use the issue templates and remove credentials, customer identifiers, audio, and transcripts from reproductions. Keep discussion respectful, specific, and focused on the work; maintainers may remove abusive or unsafe content.

## License and attribution

The API SDKs retain the [MIT License](LICENSE). Contributions intentionally submitted for inclusion are provided under that license unless an existing written agreement states otherwise. Preserve copyright and attribution notices and disclose third-party material.

The root `LICENSE` and `NOTICE` are canonical. Keep the copies in `python-sdk/` and `typescript-sdk/` identical so each package builds independently; `scripts/build` verifies those exact contents in the Python source archive, wheel, and npm archive. Include `LICENSE` and `NOTICE` in both distribution configurations and keep their declared license consistent.
