# Python Conventions

Use the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for new handwritten Python, including descriptive names, explicit ownership, and Google-style public docstrings. Preserve Python 3.9 runtime compatibility; release tooling runs separately on Python 3.12.

## Generated and handwritten code

Generated APIs/models and transport infrastructure follow OpenAPI Generator output and the repository's patch scripts. Do not reformat that output or rewrite its imports by hand. Change the generator boundary and regenerate when its behavior must change. [Architecture](architecture.md) identifies the owning modules.

Match surrounding code for focused edits to existing handwritten modules. The imported SDK uses two-space indentation in several modules; do not mix a repository move with a formatting rewrite. Use four spaces and double quotes in new Python modules and keep public names compatible.

## Imports, types, and errors

Prefer absolute owning-module imports in new handwritten code; keep public reexports deliberate. Preserve the generated API/model export contract in `coval_sdk/__init__.py` rather than applying the Agent SDK's restricted facade to this package.

Annotate handwritten public parameters and return values. Keep `Any` at dynamic JSON or transport boundaries and validate values before relying on their shapes. Do not adopt syntax or standard-library APIs unavailable on Python 3.9 in runtime modules.

Use Google-style `Args:`, `Returns:`, `Yields:`, `Raises:`, and `Attributes:` sections when they help explain public behavior. Describe errors, units, ownership, and cleanup without repeating annotations. Keep comments at the constraint they explain and follow [comment review](../CONTRIBUTING.md#documentation-and-comments).

## Validation

Follow [Contributing](../CONTRIBUTING.md#setup-and-checks) for Python tests, builds, metadata checks, and installed-wheel validation. The Python package retains its existing Ruff settings; this repository does not currently configure the Agent SDK's repository-wide Ruff formatter, strict Pyright gate, or voice-runtime architecture checker. The conventions above require review; do not describe them as automated enforcement.
