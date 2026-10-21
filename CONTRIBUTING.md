# Contributing

Use a feature branch from `main` and open a pull request describing the behavior and validation. Keep package identities and existing public APIs stable across maintenance changes. Squash-merge using a Conventional Commit PR title; `fix:`/`perf:` release a patch, `feat:` a minor, and `!`/`BREAKING CHANGE:` a major. Semantic Release owns both package versions, the changelog, and release tags. Do not bump versions in feature or regeneration PRs.

## Setup and checks

Use Python 3.12, Node.js 22 or newer, and Java 21 for code generation. The packages retain their supported Python 3.9+ and Node.js 18+ ranges.

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
