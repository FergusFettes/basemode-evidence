# Revocations and Releases

Accepted evidence is append-only. When a producer bug or privacy problem is discovered, maintainers
add `revocations/v1/<bundle-id>.json` instead of editing the contribution or rewriting Git history.

```json
{
  "schema_version": 1,
  "bundle_id": "01992df4-6c28-72f0-a67e-15fc23e6a912",
  "revoked_at": "2026-09-01T12:00:00Z",
  "reason": "producer_bug"
}
```

Reasons are restricted to `producer_bug`, `privacy_issue`, `duplicate`, and `invalid_data`. The
compiler excludes matching evidence from totals, records its revoked status in provenance, and keeps
the structured revocation in SQLite.

On pushes to `main` and on a daily schedule, CI reruns lint and tests, compiles the ledger, uploads a
workflow artifact, and replaces the assets on the rolling `dataset-latest` GitHub Release. Consumers
should verify `SHA256SUMS` and use release assets rather than crawling contribution files.
