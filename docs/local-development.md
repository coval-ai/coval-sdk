# Local Development

Use Python 3.12, uv, and Node.js 22 or newer for development; use Java 21 for OpenAPI generation. Runtime packages retain Python 3.9+ and Node.js 18+ support.

## Editable installation

```sh
scripts/install
npm ci --prefix typescript-sdk
.venv/bin/python -c "import coval_sdk"
npm run build --prefix typescript-sdk
```

The root `.venv` contains the editable Python SDK and release tools. Use `.venv/bin/python` explicitly. `PYTHON_VERSION` selects the interpreter when creating a fresh environment. TypeScript compiles source into `typescript-sdk/dist/`; rebuild after changes when testing compiled output.

Installation, imports, tests, type checks, and builds do not need Coval credentials. Offline generation additionally needs explicit synthetic or verified spec files; automated generation downloads the backend publication without a docs token; [Contributing](../CONTRIBUTING.md#generate-clients) describes setup.

## Checks and builds

```sh
scripts/check
scripts/build
```

`scripts/check` runs Python tests and TypeScript typechecking/tests, builds both packages, validates package metadata and legal files, then exercises clean installations outside the checkout. `scripts/build` writes the Python source archive and wheel to `dist/python/` and the npm archive to `dist/npm/`. The Python build creates its wheel from the source distribution. Neither command uploads artifacts.

For release changes, also run `.venv/bin/python -m pytest release_tests -q` on Python 3.12. For a focused language edit or prose-only change, use the bounded checks in [Contributing](../CONTRIBUTING.md#setup-and-checks).

## Use the SDKs in another project

Install the Python checkout with `uv pip install --python /path/to/consumer/.venv/bin/python -e /path/to/coval-sdk/python-sdk`. For package acceptance, build and install `dist/python/coval_sdk-*.whl` into that environment instead.

Install the built npm archive with `npm install /path/to/coval-sdk/dist/npm/coval-sdk-*.tgz` from the consumer project, then run its relevant checks. Editable or source-import success does not prove a distribution includes all required files.

## Live checks

Select the intended API root and workspace explicitly, use synthetic fixtures, and record the source/artifact revision and terminal outcome. Store credentials outside Git and sanitize diagnostic output. A live API check needs existing authorization for the selected environment; offline checks remain the default feedback loop.
