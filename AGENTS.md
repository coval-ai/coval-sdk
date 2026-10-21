# Coding agent guidance

- Read `README.md`, `CONTRIBUTING.md`, and any closer guidance before editing.
- Keep Python `coval-sdk` / `coval_sdk` and TypeScript `@coval/sdk` identities and public APIs stable.
- Generated clients belong in `python-sdk/src/coval_sdk/api`, `python-sdk/src/coval_sdk/models`, and `typescript-sdk/src/generated`. Prefer source-contract or generator fixes over edits that regeneration would erase.
- Preserve hand-written wrappers, compatibility specs, dependency pins, and regression assertions during extraction.
- Run the affected SDK checks from `CONTRIBUTING.md`; use synthetic local data and no live API calls for automated validation.
- Follow `docs/releasing.md` before changing release versions, publishing, or enabling migration gates. Package publication and visibility changes require user authorization.
- Keep PRs reviewable and preserve their draft state. Never commit credentials or customer data.
