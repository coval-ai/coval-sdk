# Security Policy

## Report privately

Do not open a public issue with credentials, exploitable details, customer data, audio, or transcripts. If the repository's Security tab offers **Report a vulnerability**, use that private reporting channel.

If private GitHub reporting is unavailable, use the contact details published on [Coval's website](https://www.coval.ai/) to request a private security reporting channel. Start with a request to coordinate privately, and share sensitive reproduction details only after a maintainer confirms the channel.

Include the SDK version or commit, Python or Node.js version, affected entry point, impact, and a minimal synthetic reproduction. Explain whether the issue affects API keys, workspace isolation, request handling, dependencies, or conversation data. Do not include live credentials or other people's recordings.

## Supported versions

Maintainers assess reports against published SDK versions and the current development branch, including whether a fix or backport is appropriate. No response-time or bounty commitment is made by this document.

## Handling data

Keep credentials in the environment or an approved secret source. Request payloads, diagnostic output, and errors may contain private conversation data. Use synthetic fixtures for tests and sanitize diagnostics before sharing them.

Maintainers must confirm a working private reporting channel before making the repository public; see [release preparation](docs/releasing.md).
