# basemode-evidence

[![CI](https://github.com/FergusFettes/basemode-evidence/actions/workflows/ci.yml/badge.svg)](https://github.com/FergusFettes/basemode-evidence/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://fergusfettes.github.io/basemode-evidence/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Public, append-only, privacy-preserving aggregates of real basemode endpoint calls.

The repository validates one-file contribution pull requests and compiles accepted bundles into
deterministic JSON and SQLite datasets. It never accepts prompts, generated text, individual call
records, stable user identifiers, or provider credentials.

The [documentation](https://fergusfettes.github.io/basemode-evidence/) describes the contribution
contract, privacy boundary, validation policy, compiled artifacts, and release process.

> [!IMPORTANT]
> `schemas/contribution-v1.schema.json` is a provisional pinned schema matching the current
> documented contract. It will be replaced by the canonical basemode-generated schema and fixtures once
> that exporter lands. Existing schema versions remain pinned after publication.

## Contributing evidence

A contribution pull request adds exactly one file:

```text
contributions/v1/YYYY/MM/<bundle-id>.json
```

The year and month come from `window_end`, and the filename is the bundle's UUID. A contribution PR
may not change documentation, code, workflows, schemas, revocations, or previously accepted
evidence. Validate an export locally with:

```bash
basemode-evidence validate contributions/v1/2026/08/<bundle-id>.json
```

GitHub accounts make pull requests attributable. Evidence is content-free and privacy-preserving,
not anonymous. The schema rejects unknown fields, including prompts, responses, hashes, exception
messages, credentials, account and installation identifiers, local paths, and individual events.

Current defensive limits are 1 MB per file, 1,000 observation rows, 31 days per window, 128
characters per endpoint/strategy identifier, and 24 hours of future clock skew. Changes to these
limits are repository validation policy, not contribution schema changes.

## Compiled dataset

Run `basemode-evidence compile` to create these files in `dist/`:

- `endpoint_summary.json`: totals and rates by endpoint, with source and strategy counts;
- `endpoint_evidence.sqlite`: normalized bundles, observations, failures, and revocations;
- `provenance.json`: source paths, hashes, inclusion status, and revocations;
- `manifest.json` and `SHA256SUMS`: artifact metadata and independently verifiable hashes.

Submitted p50/p95 values remain contribution-level summaries. They are never averaged or presented
as exact global percentiles. Daily and Parquet artifacts are deferred because multi-day aggregate
bundles cannot be truthfully separated into daily observations.

Compilation validates all ledger entries and is byte-stable for the same repository tree. Its build
time is derived from the evidence rather than the wall clock. No provider credentials or network
access are used.

## Revocations

Maintainers revoke evidence without rewriting history by adding
`revocations/v1/<bundle-id>.json`. Reasons are enumerated (`producer_bug`, `privacy_issue`,
`duplicate`, or `invalid_data`). The compiler excludes the bundle while preserving both records in
provenance and SQLite.

## Development

```bash
uv sync --locked --group dev
make check
```

Install the optional local hooks with `uv run pre-commit install`. The same lint, test, build, and
wheel-install checks run in CI on every code change.

Build or serve the documentation locally with `make docs-build` or `make docs-serve`. For repository
orientation and change checklists, see the [agent quickstart](https://fergusfettes.github.io/basemode-evidence/Agent-Quickstart/).
