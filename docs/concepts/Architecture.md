# Architecture

The project separates local observation from public aggregation.

```text
basemode recorder
  -> local aggregation and privacy filtering
  -> one deterministic contribution bundle
  -> contribution-only GitHub pull request
  -> schema, semantic, privacy, and repository-boundary validation
  -> append-only contribution ledger
  -> deterministic compiler
  -> rolling GitHub Release
```

## Ownership boundary

Basemode owns local call recording, operation and attempt semantics, failure classification,
aggregation, privacy filtering, contribution preview/export, the canonical bundle schema and
fixtures, optional pull-request orchestration, and importing compiled snapshots.

This repository owns the public ledger, pinned schemas, defensive validation, contribution-only PR
policy, compilation, provenance, revocation, and published datasets. Validation and compilation do
not import basemode's provider stack, require API keys, or make network calls.

## Repository layout

```text
schemas/                         pinned contribution and revocation schemas
contributions/v1/YYYY/MM/       immutable accepted bundles
revocations/v1/                 structured corrections by bundle ID
src/basemode_evidence/          validator, compiler, and CLI
tests/                           fixtures and regression coverage
docs/                            this wiki
dist/                            ignored build output
```

Contribution PRs add exactly one file below `contributions/v1/`. Code, policy, schema, workflow, and
revocation changes use ordinary maintainer PRs. This distinction makes parallel evidence submissions
conflict-free without preventing repository maintenance.

## Deferred capabilities

Daily output is deferred because a multi-day aggregate cannot be truthfully divided into daily rows.
Parquet is deferred with it. Global p50/p95 values are also deferred until the schema carries a
mergeable histogram or sketch; submitted percentiles remain contribution-level summaries.
