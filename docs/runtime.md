# Runtime Contracts

Both clients default to `https://api.coval.dev/v1` and accept an alternate API root. The wrappers require an API key and send it in the lowercase `x-api-key` header. Applications own credential retrieval and environment selection.

## Requests and retries

The default retry policies permit `GET`, `HEAD`, and `OPTIONS` and recognize `408`, `429`, `500`, `502`, `503`, and `504` as retryable statuses. Preserve that method boundary: a failed mutation must not silently become a repeated write. Callers can explicitly configure retry behavior through each language's existing options.

Python configures urllib3 retries, respects `Retry-After`, and uses two retries by default. It bounds each request with a 10-second connect and 60-second read timeout by default, because urllib3 otherwise waits forever on a stalled connection; callers may change or disable it, and a per-call `_request_timeout` takes precedence. Its wrapper expires idle pooled connections after five seconds by default; callers may change or disable expiry. `connection_stats` records pool outcomes. `close()` clears pooled connections, and the client context manager calls it on exit.

TypeScript wraps fetch with three total attempts by default, exponential backoff, jitter, and a five-second delay cap. It honors `Retry-After` within that cap. `retry: false` disables retries; callers can supply fetch and middleware. Transport statistics and the optional `onDebug` callback expose diagnostics without configuring application logging.

## Responses and pagination

Python preserves the generated exception hierarchy. Its deserialization patches handle invalid list entries according to `strict_response_validation`; [Python usage](../python-sdk/README.md) describes the caller-facing choice. Python pagination supports mappings and generated models, and rejects repeated page tokens.

TypeScript reports failed HTTP responses through `CovalApiError` and exhausted network failures through `CovalNetworkError`. Its async `paginate` helper follows caller-supplied item/token selectors until no token remains or `maxPages` is reached; `collectAll` collects those items.

Keep these behaviors covered through the public clients and helpers. Tests use synthetic responses and local collaborators; successful offline checks do not establish behavior of a selected hosted environment. Sanitize errors and diagnostics before sharing them; follow [Security](../SECURITY.md) for sensitive reports.
