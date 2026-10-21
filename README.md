# Coval API SDKs

Python and TypeScript clients for the Coval API, with typed models, authentication, retries, and pagination.

| Language | Install | Guide |
| --- | --- | --- |
| Python 3.9+ | `pip install coval-sdk` | [Python SDK](python-sdk/README.md) |
| TypeScript / Node.js 18+ | `npm install @coval/sdk` | [TypeScript SDK](typescript-sdk/README.md) |

Both packages use `https://api.coval.dev/v1` by default and authenticate with your Coval API key. See the language guides for complete examples and configuration.

For streaming voice agents, use the separate [Coval Agent SDK](https://github.com/coval-ai/coval-agent-sdk). Application examples live in [coval-examples](https://github.com/coval-ai/coval-examples).

## Development

See [Contributing](CONTRIBUTING.md) for setup, tests, and OpenAPI generation, and [Releasing](docs/releasing.md) for registry publishing and repository migration.

The initial SDK source was extracted from [coval-examples at `3b4e2b7`](https://github.com/coval-ai/coval-examples/tree/3b4e2b74b491fc0db09cbd8d5772d94f1391cf5d). Package names, versions, and runtime interfaces are preserved. Earlier history remains in that repository.

## Support

[API reference](https://docs.coval.dev/api-reference) · [Issues](https://github.com/coval-ai/coval-sdk/issues) · support@coval.dev

Both packages are MIT-licensed.
