# Contribution Format

A v1 contribution is deterministic UTF-8 JSON with this shape:

```json
{
  "schema_version": 1,
  "bundle_id": "01992df4-6c28-72f0-a67e-15fc23e6a912",
  "generated_at": "2026-08-31T12:00:00Z",
  "basemode_version": "0.2.0",
  "window_start": "2026-08-30T00:00:00Z",
  "window_end": "2026-08-31T00:00:00Z",
  "observations": [
    {
      "endpoint": "anthropic/claude-sonnet-4-6",
      "strategy": "system",
      "source": "loom",
      "source_version": "0.8.0",
      "operations": 184,
      "successful_operations": 181,
      "initial_attempts": 184,
      "successful_initial_attempts": 176,
      "recovered_operations": 5,
      "attempts": 191,
      "failures": {"timeout": 2, "empty_response": 3, "rate_limit": 1},
      "latency_ms": {"count": 181, "p50": 1840, "p95": 6210},
      "ttft_ms": {"count": 178, "p50": 720, "p95": 2400},
      "input_tokens": 43120,
      "output_tokens": 29842,
      "cost_usd": 1.2842
    }
  ]
}
```

## Bundle fields

`schema_version` is exactly `1`. `bundle_id` is a locally generated UUID used for idempotency.
Timestamps are UTC and the aggregation window starts before it ends. `observations` is non-empty.

Rows are grouped by provider-qualified endpoint, basemode strategy, source application, optional
source version, and the bundle window. Allowed v1 sources are `cli`, `python`, `server`, `loom`, and
`verification`.

`operations` counts logical continuation requests; `successful_operations` counts those ultimately
returning content. `initial_attempts` and `successful_initial_attempts` describe the first physical
provider request. `recovered_operations` counts successful operations needing another attempt, and
`attempts` counts all physical requests.

Failure keys are restricted to `authentication`, `quota`, `rate_limit`, `timeout`, `network`,
`provider_unavailable`, `invalid_request`, `empty_response`, `content_filter`, `provider_error`,
`cancelled`, and `unknown`.

Latency and TTFT contain only `count`, `p50`, and `p95`. Latency is measured once per logical
operation, so its `count` cannot exceed `successful_operations`; TTFT is measured on each provider
request that produced a token, so its `count` is bounded by `attempts` instead. Token and cost totals are optional. Basemode's
local `prompt_tokens` and `completion_tokens` intentionally serialize as `input_tokens` and
`output_tokens` in this public schema.

The machine-enforced contract is the pinned
[`schemas/contribution-v1.schema.json`](https://github.com/FergusFettes/basemode-evidence/blob/main/schemas/contribution-v1.schema.json).
