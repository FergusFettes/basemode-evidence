# basemode-evidence specification

## Purpose

`basemode-evidence` is the public, append-only repository for privacy-preserving
aggregates of real basemode endpoint calls. It accepts evidence bundles through
GitHub pull requests, validates them, and publishes compiled datasets for
humans and tools.

This repository does not call model providers, collect prompts, implement
basemode verification, or decide how a local application records calls. Those
responsibilities remain in `basemode`.

## Initial scope

Version 1 contains endpoint-call evidence only:

- how many logical continuation operations were requested;
- how many ultimately returned content;
- how many physical provider attempts were made;
- how often the initial attempt succeeded;
- how often recovery was required;
- safe failure categories;
- aggregate latency, time-to-first-token, token usage, and cost where known;
- endpoint, strategy, source application, and software versions.

User flags, edits, branch selection, prose quality, prompts, and generated text
are outside the v1 schema. Quality data may be added later as a separate,
optional dataset.

Poisoning resistance beyond basic validation and manual PR review is explicitly
deferred. Preserve provenance so stronger trust policies can be added later.

## Repository layout

The implementation should converge on:

```text
basemode-evidence/
├── SPEC.md
├── README.md
├── pyproject.toml
├── schemas/
│   └── contribution-v1.schema.json
├── contributions/
│   └── v1/
│       └── YYYY/
│           └── MM/
│               └── <bundle-id>.json
├── src/basemode_evidence/
│   ├── validate.py
│   ├── compile.py
│   └── cli.py
├── tests/
├── .github/workflows/
│   ├── validate-contribution.yml
│   └── publish-dataset.yml
└── dist/                         # ignored; release artifacts are built here
```

Contribution PRs add exactly one new file under `contributions/v1/YYYY/MM/`.
They must not edit an index or another contributor's file. This keeps parallel
submissions conflict-free.

## Contribution bundle v1

Bundles are JSON, UTF-8, deterministic, and contain no free-text fields beyond
strictly enumerated identifiers. A representative payload is:

```json
{
  "schema_version": 1,
  "bundle_id": "01992df4-6c28-72f0-a67e-15fc23e6a912",
  "generated_at": "2026-09-07T00:00:00Z",
  "basemode_version": "0.2.0",
  "window_start": "2026-08-31T00:00:00Z",
  "window_end": "2026-09-07T00:00:00Z",
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
      "failures": {
        "timeout": 2,
        "empty_response": 3,
        "rate_limit": 1
      },
      "latency_ms": {"count": 181, "p50": 1840, "p95": 6210},
      "ttft_ms": {"count": 178, "p50": 720, "p95": 2400},
      "input_tokens": 43120,
      "output_tokens": 29842,
      "cost_usd": 1.2842
    }
  ]
}
```

The canonical schema must be supplied by `basemode`, because basemode owns the
meaning and serialization of call observations. This repository keeps a pinned
copy so old PRs remain independently validatable.

### Required bundle fields

- `schema_version`: integer, initially exactly `1`.
- `bundle_id`: UUID/UUIDv7 string generated locally and used for idempotency.
- `generated_at`: UTC timestamp for bundle construction.
- `basemode_version`: producing basemode version.
- `window_start`, `window_end`: UTC aggregation window; start is before end.
- `observations`: non-empty list of aggregate rows.

### Observation dimensions

Rows are grouped by the following dimensions:

- normalized, provider-qualified `endpoint`;
- basemode strategy;
- source application (`cli`, `python`, `server`, `loom`, `verification`, or a
  future allow-listed value);
- source application version, where known;
- bundle time window.

Do not add account, document, tree, prompt, user, installation, hostname,
region, or arbitrary tag dimensions in v1.

### Outcome fields

- `operations`: logical basemode continuation operations.
- `successful_operations`: operations that ultimately returned content.
- `initial_attempts`: physical attempts marked `initial`.
- `successful_initial_attempts`: initial attempts that returned content.
- `recovered_operations`: successful operations that required another attempt.
- `attempts`: all physical provider requests.
- `failures`: counts keyed by basemode's allow-listed failure taxonomy.

Optional metrics are totals or fixed aggregate summaries only. No individual
event timestamps or measurements are accepted.

### Failure taxonomy

The v1 allow-list should match basemode's public schema. Expected categories:

```text
authentication
quota
rate_limit
timeout
network
provider_unavailable
invalid_request
empty_response
content_filter
provider_error
cancelled
unknown
```

The schema must be versioned if this vocabulary changes incompatibly.

## Privacy constraints

CI must reject any bundle containing unknown fields. This is the primary
privacy boundary: an exporter cannot accidentally add content-bearing metadata
that the evidence repository silently retains.

The format must never accept:

- prompt or response text;
- prompt or response hashes/fingerprints;
- provider exception messages or bodies;
- keys, tokens, authorization headers, or account identifiers;
- IP addresses, hostnames, local paths, document IDs, tree IDs, or node IDs;
- stable installation or user identifiers;
- arbitrary request parameters;
- individual-call timestamps.

GitHub PRs are associated with a GitHub account and therefore are not fully
anonymous. Documentation must describe contributions as content-free and
privacy-preserving, not anonymous.

## Validation

Provide both a library function and CLI:

```bash
basemode-evidence validate path/to/bundle.json
basemode-evidence validate-pr --base BASE_SHA --head HEAD_SHA
```

Validation includes:

1. The PR adds exactly one contribution JSON file and does not modify accepted
   evidence, schema, workflow, compiler, or repository configuration.
2. The path year/month agrees with `window_end`.
3. The filename stem equals `bundle_id`.
4. The payload validates against the pinned JSON Schema.
5. No unknown fields exist at any level.
6. The bundle ID does not already exist in repository history/current files.
7. Counts are non-negative integers and satisfy:
   - `successful_operations <= operations`;
   - `recovered_operations <= successful_operations`;
   - `successful_initial_attempts <= initial_attempts`;
   - `initial_attempts <= attempts`;
   - summed failures do not exceed attempts.
8. Metric counts do not exceed the population they describe.
9. Percentiles are non-negative and `p50 <= p95`.
10. Timestamps are UTC and the aggregation window is sensible.
11. Endpoints and enum-like strings meet length and character restrictions.
12. The file and row count are below conservative limits.
13. A secret/content scanner finds no suspicious keys, token-like values, long
    natural-language strings, URLs, filesystem paths, or unexpected entropy.

The PR workflow should comment with a human-readable summary: window,
endpoints, operations, attempts, failures, schema version, and confirmation
that no content-bearing fields were accepted.

Manual maintainer approval and merge are sufficient for v1.

## Compilation

The compiler reads all accepted, non-revoked bundles and produces deterministic
artifacts:

```text
endpoint_summary.json
endpoint_daily.parquet
endpoint_evidence.sqlite
provenance.json
SHA256SUMS
```

Minimum compiled views:

- totals by endpoint;
- daily totals by endpoint;
- logical success rate;
- initial-attempt success rate;
- recovery rate;
- failures by category;
- latency and TTFT summaries where mergeable;
- token and cost totals where supplied;
- counts by source and strategy;
- bundle count and last-observed time;
- controlled verification and organic usage kept distinguishable.

Do not manufacture precise global percentiles by averaging submitted
percentiles. Either define a mergeable histogram/sketch in a later schema or
publish contribution-level percentile summaries with clear semantics. For v1,
count-weighted approximations must be labelled as approximations if retained.

Compilation must be idempotent and stable for the same repository tree.

## Publication

On merge to `main`, or on a scheduled workflow, compile the dataset and publish
the artifacts to a rolling GitHub Release. The release assets are the supported
machine-consumption interface; consumers should not scan contribution files.

Also publish a small manifest containing:

- dataset schema version;
- source commit;
- build time;
- row and bundle counts;
- artifact names, sizes, and SHA-256 hashes.

GitHub Pages may later render the compiled summary, but a dashboard is not
required for the initial implementation.

## Revocation

Do not rewrite Git history when a producer bug is discovered. Add a versioned
revocation mechanism keyed by bundle ID, with a short structured reason. The
compiler excludes revoked bundles and lists them in `provenance.json`.

The exact revocation file shape can be finalized during implementation, but it
must be tested before the first public contribution is accepted.

## Relationship with basemode

Basemode owns:

- local call recording;
- operation/attempt semantics;
- failure classification;
- aggregation and privacy filtering;
- contribution preview/export;
- the canonical bundle schema and example fixtures;
- optional GitHub PR orchestration;
- importing compiled public snapshots.

This repository owns:

- the public contribution ledger;
- defensive validation of exported bundles;
- PR-only intake policy;
- compilation across accepted contributions;
- published public dataset artifacts;
- provenance and revocation.

The validator should reuse a pinned basemode schema but must not import
basemode's provider stack or require API keys.

## Initial implementation order

1. Scaffold the repository, tests, linting, and CI.
2. Add the pinned contribution-v1 schema and valid/invalid fixtures.
3. Implement strict file and semantic validation.
4. Add the contribution-only PR workflow and summary comment.
5. Implement deterministic JSON and SQLite compilation.
6. Add Parquet only if its dependency cost is acceptable for this repository.
7. Implement revocations and provenance output.
8. Publish a release from fixture/test contributions before accepting real PRs.
9. Document manual and `basemode contribute pr` submission paths.

## Acceptance criteria

- A valid basemode-generated bundle can be submitted as a one-file PR.
- CI rejects schema drift, content-like fields, invalid arithmetic, duplicate
  bundles, and edits outside the contribution path.
- Compilation is deterministic and excludes revoked bundles.
- Release artifacts can be downloaded and independently checksum-verified.
- No model-provider credentials or network calls are needed to validate or
  compile evidence.
- The repository remains useful without a hosted ingestion service.
