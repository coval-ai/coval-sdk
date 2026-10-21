# Developer API

Install Python as `coval-sdk` and import `coval_sdk`; install TypeScript as `@coval/sdk`. The language guides contain runnable examples and configuration: [Python](../python-sdk/README.md) and [TypeScript](../typescript-sdk/README.md).

## Public surfaces

Python's `CovalClient` exposes generated API instances as snake-case properties, such as `client.agents` and `client.uploaded_conversations`. Generated API classes, request/response models, configuration, and low-level clients remain public. `paginate` iterates token-paginated responses. Use a client context manager or call `close()` to release pooled connections.

TypeScript's `CovalClient` exposes generated API instances as camel-case properties, such as `client.agents` and `client.uploadedConversations`. The root module exports the wrapper, generated operations/models, errors, retry/auth helpers, statistics, and pagination helpers. `@coval/sdk/generated` also exposes the generated surface directly.

Do not hide or rename existing generated exports merely to match the Agent SDK's private-adapter architecture. These published API clients have their own compatibility contract.

## Compatibility

The [legacy contracts](../legacy-specs/README.md) retain older conversation, simulation, and monitor APIs alongside canonical surfaces. Preserve those paths and method names until their documented major-release retirement conditions are met. Keep Python and TypeScript semantically aligned while using their existing language-specific names and calling conventions.

Changes to operations, models, serialization, exports, or defaults must update affected examples and regression coverage. Label proposed interfaces as proposals until implemented; this page describes supported behavior. [Runtime contracts](runtime.md) describes authentication, retry eligibility, pagination, and errors.
