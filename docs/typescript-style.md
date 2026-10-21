# TypeScript Conventions

Keep handwritten TypeScript under `typescript-sdk/src/` and generated code under `typescript-sdk/src/generated/`. Follow existing two-space indentation, single-quoted imports, explicit exports, and the ESM `.js` import suffix used by the compiler output. Preserve the package's Node.js 18+ runtime contract separately from development-tool requirements.

## Ownership and types

Keep authentication, retries, errors, statistics, and pagination in their existing owning modules. Use generated request/response types at API boundaries and narrow unknown failures before reading their properties. Prefer explicit interfaces for public options and preserve the generated types exported through the root facade and `@coval/sdk/generated`.

Do not reformat generated files by hand. Change source specs, generator configuration, or patch scripts and regenerate; [Architecture](architecture.md) explains that path. Keep provider frameworks and application configuration outside this SDK.

## Public documentation and tests

Document meaningful defaults, error behavior, units, and caller ownership with JSDoc where useful. Follow [comment review](../CONTRIBUTING.md#documentation-and-comments). Test observable requests/results, retry eligibility, failures, and public exports using synthetic data and local collaborators.

`npm run typecheck --prefix typescript-sdk` checks the configured types without emitting files; `npm run build --prefix typescript-sdk` compiles distribution files. `npm test --prefix typescript-sdk` runs Vitest. `scripts/check` also installs a built npm archive outside the checkout. Formatting and architectural choices require review; no TypeScript formatter or architecture linter is configured.
